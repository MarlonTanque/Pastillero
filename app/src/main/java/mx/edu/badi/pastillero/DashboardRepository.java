package mx.edu.badi.pastillero;

import android.content.Context;
import androidx.lifecycle.MutableLiveData;
import androidx.work.WorkManager;
import com.google.firebase.database.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;
import org.json.*;

/** Fachada V2: React solicita operaciones; solo Java toca Room, Authentication y Firebase. */
public final class DashboardRepository implements AutoCloseable {
    public final Repository legacy;
    public final MutableLiveData<Long> changes = new MutableLiveData<>(0L);
    private final Context context;
    private final PastilleroDatabase database;
    private final PastilleroDao dao;
    private final ExecutorService disk = Executors.newSingleThreadExecutor();
    private DatabaseReference cloud;
    private ValueEventListener cloudListener;
    private volatile boolean closed;
    private volatile JSONObject deviceState = new JSONObject();
    private long lastWeekStart;
    public DashboardRepository(Context c) {
        context = c.getApplicationContext();
        database = PastilleroDatabase.get(c);
        dao = database.dao();
        legacy = new Repository(c);
    }
    public void refreshAuthorization() {
        if (closed)
            return;
        if (!legacy.isAuthorized()) {
            if (cloud != null && cloudListener != null)
                cloud.removeEventListener(cloudListener);
            cloud = null;
            cloudListener = null;
            deviceState = new JSONObject();
            if (legacy.uid != null)
                WorkManager.getInstance(context).cancelUniqueWork("program-v2-" + legacy.scope);
            return;
        }
        if (cloudListener != null)
            return;
        cloud = FirebaseDatabase.getInstance()
                    .getReference("devices")
                    .child(BuildConfig.DEVICE_ID)
                    .child("v2");
        cloudListener = new ValueEventListener() {
            public void onDataChange(DataSnapshot snapshot) {
                if (closed || !legacy.isAuthorized())
                    return;
                disk.execute(() -> {
                    try {
                        if (closed || !legacy.isAuthorized())
                            return;
                        Object raw = snapshot.child("state").getValue();
                        deviceState = raw instanceof Map
                            ? new JSONObject((Map < ?, ? >) raw) : new JSONObject();
                        for (DataSnapshot s : snapshot.child("events").getChildren()) {
                            DoseEvent e = s.getValue(DoseEvent.class);
                            if (e == null || s.getKey() == null)
                                continue;
                            e.scope = legacy.scope;
                            e.eventId = s.getKey();
                            if (dao.insertEvent(e) != -1)
                                Alerts.event(context, e);
                        }
                        for (DataSnapshot result :
                            snapshot.child("commandResults/simulation").getChildren()) {
                            if (result.getKey() != null && result.getValue() instanceof Map)dao.commandResult(legacy.scope,result.getKey(),
                                String.valueOf(result.child("status").getValue())+" · "+String.valueOf(result.child("reason").getValue()),new JSONObject((Map<?,?>)result.getValue()).toString());
                        }
                        importProgram(snapshot.child("program"), false);
                        changed();
                    } catch (Exception e) {
                        legacy.connection.postValue(
                            "Datos V2 no disponibles o inválidos; Room se conserva");
                    }
                });
            }
            public void onCancelled(DatabaseError error) {
                legacy.connection.postValue("Firebase V2: " + error.getMessage());
            }
        };
        cloud.addValueEventListener(cloudListener);
        ProgramWorker.enqueue(context, legacy.uid);
    }
    private DevicePreferences preferences() {
        DevicePreferences p = dao.preferences(legacy.scope);
        if (p == null) {
            p = new DevicePreferences();
            p.scope = legacy.scope;
        }
        return p;
    }
    private void canEdit() {
        if (legacy.uid != null && !legacy.isAuthorized())
            throw new SecurityException("Espera la comprobación de permisos");
    }
    private void edited() {
        ProgramOutbox p = dao.program(legacy.scope);
        if (p == null) {
            p = new ProgramOutbox();
            p.scope = legacy.scope;
        }
        p.edited = true;
        p.dirty = false;
        p.token = UUID.randomUUID().toString();
        p.status = "Cambios guardados en Room; falta publicar";
        dao.saveProgram(p);
    }
    private void changed() {
        changes.postValue(System.nanoTime());
    }
    public void request(
        String action, JSONObject payload, Consumer<JSONObject> success, Consumer<String> failure) {
        if (closed)
            return;
        disk.execute(() -> {
            try {
                if (closed)
                    return;
                if (!action.equals("snapshot"))
                    canEdit();
                switch (action) {
                    case "saveMedication": {
                        Medication m = BridgeProtocol.medication(
                            payload, legacy.scope, preferences().positions);
                        List<Medication> meds = dao.medications(legacy.scope);
                        if (meds.size() >= 12
                            && meds.stream().noneMatch(x -> x.medicationId.equals(m.medicationId)))
                            throw new IllegalArgumentException("Máximo doce medicamentos");
                        database.runInTransaction(() -> {
                            dao.saveMedication(m);
                            edited();
                        });
                        break;
                    }
                    case "deleteMedication": {
                        BridgeProtocol.keys(payload, "id");
                        String id = BridgeProtocol.string(payload, "id");
                        if (!id.matches("[A-Za-z0-9-]{1,36}"))
                            throw new IllegalArgumentException("ID inválido");
                        database.runInTransaction(() -> {
                            dao.deleteMedication(legacy.scope, id);
                            edited();
                        });
                        break;
                    }
                    case "savePreferences": {
                        DevicePreferences p = BridgeProtocol.preferences(payload, legacy.scope);
                        for (Medication m : dao.medications(legacy.scope))
                            ScheduleEngine.validate(m, p.positions);
                        database.runInTransaction(() -> {
                            dao.savePreferences(p);
                            edited();
                        });
                        break;
                    }
                    case "publish": {
                        BridgeProtocol.keys(payload);
                        DevicePreferences prefs = preferences();
                        JSONObject json = ScheduleEngine.program(
                            dao.medications(legacy.scope), prefs, System.currentTimeMillis());
                        json.put("targetMode", "simulation");
                        ProgramOutbox p = dao.program(legacy.scope);
                        if (p == null) {
                            p = new ProgramOutbox();
                            p.scope = legacy.scope;
                        }
                        p.json = json.toString();
                        p.token = UUID.randomUUID().toString();
                        p.dirty = true;
                        p.edited = false;
                        p.status = legacy.uid == null ? "Plan validado en modo local; no enviado"
                                                      : "Pendiente de acuse Firebase V2";
                        dao.saveProgram(p);
                        if (legacy.uid != null)
                            ProgramWorker.enqueue(context, legacy.uid);
                        break;
                    }
                    case "reload":
                    case "rebase": {
                        BridgeProtocol.keys(payload);
                        if (!legacy.isAuthorized() || cloud == null)
                            throw new SecurityException("Se requiere una sesión autorizada");
                        DataSnapshot remote = com.google.android.gms.tasks.Tasks.await(
                            cloud.child("program").get(), 20, TimeUnit.SECONDS);
                        if (action.equals("reload") && remote.exists())
                            importProgram(remote, true);
                        else {
                            ProgramOutbox p = dao.program(legacy.scope);
                            if (p == null) {
                                p = new ProgramOutbox();
                                p.scope = legacy.scope;
                            }
                            Long rev = remote.child("revision").getValue(Long.class);
                            p.baseRevision = rev == null ? 0 : rev;
                            p.token = UUID.randomUUID().toString();
                            p.dirty = false;
                            p.edited = true;
                            p.status = "Revisión recargada; pautas locales conservadas para "
                                + "revisar y publicar";
                            dao.saveProgram(p);
                        }
                        break;
                    }
                    case "ping":
                        BridgeProtocol.keys(payload);
                        if (!legacy.isAuthorized())
                            throw new SecurityException(
                                "Inicia sesión con el responsable para comprobar la conexión");
                        CommandWorker.queueV2(
                            context, legacy.uid, UUID.randomUUID().toString(), "PING", 0);
                        break;
                    case "retry":
                        BridgeProtocol.keys(payload);
                        if (legacy.uid != null)
                            ProgramWorker.enqueue(context, legacy.uid);
                        break;
                    case "snapshot":
                        BridgeProtocol.keys(payload, "weekStart");
                        if (payload.has("weekStart"))
                            lastWeekStart = BridgeProtocol.number(payload, "weekStart");
                        break;
                    default:
                        throw new IllegalArgumentException("Acción no admitida por el repositorio");
                }
                success.accept(snapshot(lastWeekStart));
                if (!action.equals("snapshot"))
                    changed();
            } catch (SecurityException | IllegalArgumentException e) {
                failure.accept(e.getMessage());
            } catch (Exception e) {
                failure.accept("No se pudo completar la operación; revisa fechas y conexión");
            }
        });
    }
    private JSONObject snapshot(long weekStart) throws JSONException {
        DevicePreferences prefs = preferences();
        List<Medication> meds = dao.medications(legacy.scope);
        if (weekStart == 0) {
            ZonedDateTime now = ZonedDateTime.now();
            weekStart = now.toLocalDate()
                            .minusDays(now.getDayOfWeek().getValue() - 1)
                            .atStartOfDay(now.getZone())
                            .toInstant()
                            .toEpochMilli();
        }
        long now = System.currentTimeMillis();
        if (Math.abs(weekStart - now) > 2L * 366 * 86400000L)
            throw new IllegalArgumentException("Semana fuera de rango");
        long until = Instant.ofEpochMilli(weekStart)
                         .atZone(ZoneId.systemDefault())
                         .toLocalDate()
                         .plusDays(7)
                         .atStartOfDay(ZoneId.systemDefault())
                         .toInstant()
                         .toEpochMilli();
        JSONArray medicationJson = new JSONArray(), occurrences = new JSONArray(),
                  events = new JSONArray();
        for (Medication m : meds) medicationJson.put(ScheduleEngine.medicationJson(m));
        for (ScheduleEngine.Occurrence o :
            ScheduleEngine.expand(meds, prefs.positions, weekStart, until, 4096))
            occurrences.put(o.json());
        for (DoseEvent e : dao.events(legacy.scope))
            events.put(new JSONObject()
                    .put("id", e.eventId)
                    .put("doseId", e.doseId)
                    .put("medicationId", e.medicationId)
                    .put("type", e.type)
                    .put("scheduledAt", e.scheduledAt)
                    .put("actualAt", e.actualAt)
                    .put("compartment", e.compartment)
                    .put("simulation", e.simulation));
        ProgramOutbox p = dao.program(legacy.scope);
        CommandRequest command = dao.latestV2Command(legacy.scope);
        return new JSONObject()
            .put("medications", medicationJson)
            .put("occurrences", occurrences)
            .put("events", events)
            .put("settings", ScheduleEngine.preferencesJson(prefs))
            .put("device", deviceState)
            .put("signedIn", legacy.uid != null)
            .put("authorized", legacy.isAuthorized())
            .put("simulation", true)
            .put("connection", String.valueOf(legacy.connection.getValue()))
            .put("programStatus", p == null ? "Aún no hay plan V2 publicado" : p.status)
            .put("pingStatus", command == null ? "Sin solicitudes V2" : command.status)
            .put("revision", p == null ? 0 : p.baseRevision)
            .put("pending", p != null && (p.dirty || p.edited))
            .put("now", now)
            .put("weekStart", weekStart);
    }
    private void importProgram(DataSnapshot s, boolean force) throws JSONException {
        if (!s.exists())
            return;
        ProgramOutbox local = dao.program(legacy.scope);
        if (!force && local != null && (local.dirty || local.edited))
            return;
        JSONObject j=new JSONObject((Map<?,?>)s.getValue());
        if (j.optInt("version") != 2 || !"simulation".equals(j.optString("targetMode")))
            return;
        DevicePreferences p = BridgeProtocol.preferences(j.getJSONObject("settings"), legacy.scope);
        List<Medication> imported = new ArrayList<>();
        JSONObject regimens = j.optJSONObject("regimens");
        if (regimens != null) {
            Iterator<String> it = regimens.keys();
            while (it.hasNext()) {
                String id = it.next();
                Medication m = BridgeProtocol.medication(
                    regimens.getJSONObject(id), legacy.scope, p.positions);
                if (!id.equals(m.medicationId))
                    throw new IllegalArgumentException("ID remoto inválido");
                imported.add(m);
            }
        }
        if (imported.size() > 12)
            throw new IllegalArgumentException("Exceso de pautas");
        ProgramOutbox next = new ProgramOutbox();
        next.scope = legacy.scope;
        next.baseRevision = j.getLong("revision");
        next.token = j.getString("token");
        next.json = j.toString();
        next.status = "Programa V2 recibido de Firebase";
        database.runInTransaction(() -> {
            for (Medication old : dao.medications(legacy.scope))
                dao.deleteMedication(legacy.scope, old.medicationId);
            for (Medication m : imported) dao.saveMedication(m);
            dao.savePreferences(p);
            dao.saveProgram(next);
        });
    }
    @Override
    public void close() {
        closed = true;
        if (cloud != null && cloudListener != null)
            cloud.removeEventListener(cloudListener);
        disk.shutdown();
        legacy.close();
    }
}
