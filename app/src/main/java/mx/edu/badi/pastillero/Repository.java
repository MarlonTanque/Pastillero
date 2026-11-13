package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.annotation.NonNull;
import androidx.lifecycle.MutableLiveData;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.*;
import org.json.*;
import java.util.*;
import java.util.concurrent.*;

public class Repository implements AutoCloseable {
    public final MutableLiveData<String> connection =
        new MutableLiveData<>("Modo local · sin publicar al ESP32");
    public final MutableLiveData<String> deviceState =
        new MutableLiveData<>("Estado del dispositivo no disponible");
    public final String scope, uid;
    public final PastilleroDao dao;
    private final Context context;
    // Lectura: Una cola de trabajo serial ejecuta SQL y transformación de datos fuera del hilo de pantalla.
    private final ExecutorService disk = Executors.newSingleThreadExecutor();
    private DatabaseReference root, connected, access;
    private ValueEventListener planListener, stateListener, connectionListener, resultsListener,
        accessListener;
    private ChildEventListener eventsListener;
    private volatile boolean closed;
    private volatile boolean authorized;
    private volatile boolean accessAllowed;
    private DataSnapshot lastState;
    private final android.os.Handler timer =
        new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable freshness = new Runnable() {
        @Override
        public void run() {
            if (!closed) {
                renderState();
                timer.postDelayed(this, 5000);
            }
        }
    };
    // Lectura: Abre Room y determina cuenta/ámbito; solo inicia red si existe una sesión.
    public Repository(Context c) {
        context = c.getApplicationContext();
        dao = PastilleroDatabase.get(c).dao();
        uid = PastilleroApp.cloudReady() && FirebaseAuth.getInstance().getCurrentUser() != null
            ? FirebaseAuth.getInstance().getCurrentUser().getUid()
            : null;
        scope = SyncWorker.scope(uid == null ? "local" : uid);
        if (uid != null)
            start();
    }
    // Lectura: Envía trabajo al ejecutor de disco mientras el repositorio siga abierto.
    private void task(Runnable job) {
        if (!closed)
            disk.execute(job);
    }
    // Lectura: Construye un listener reutilizable: entrega instantáneas al callback y comunica errores de lectura.
    private ValueEventListener listener(java.util.function.Consumer<DataSnapshot> receive) {
        return new ValueEventListener() {
            public void onDataChange(@NonNull DataSnapshot data) {
                if (!closed)
                    receive.accept(data);
            }
            public void onCancelled(@NonNull DatabaseError e) {
                connection.postValue("Firebase: " + e.getMessage());
            }
        };
    }
    // Lectura: Primero observa permiso enabled y comprueba ownerUid; todavía no importa datos de la caché del SDK.
    private void start() {
        root = FirebaseDatabase.getInstance().getReference("devices").child(BuildConfig.DEVICE_ID);
        access = FirebaseDatabase.getInstance().getReference("access/users").child(uid);
        accessListener = new ValueEventListener() {
            public void onDataChange(@NonNull DataSnapshot record) {
                if (closed)
                    return;
                accessAllowed =
                    Boolean.TRUE.equals(record.child("enabled").getValue(Boolean.class));
                if (!accessAllowed) {
                    denyAccess();
                    return;
                }
                if (authorized)
                    return;
                // Poder leer el permiso propio no concede acceso: también se verifica el vínculo al dispositivo.
                root.child("ownerUid")
                    .get()
                    .addOnSuccessListener(s -> {
                        if (closed || !accessAllowed || authorized)
                            return;
                        // Lectura: Leer el permiso propio no basta: la cuenta también debe estar vinculada como
                        // Lectura: responsable de este dispositivo.
                        if (!uid.equals(s.getValue(String.class))) {
                            connection.postValue("Esta cuenta no está vinculada como responsable");
                            return;
                        }
                        authorized = true;
                        startAuthorized();
                    })
                    .addOnFailureListener(e -> {
                        if (!closed)
                            connection.postValue(
                                "No se pudo comprobar el acceso; inicia sesión de nuevo si fue "
                                + "restablecido. El historial local sigue disponible");
                    });
            }
            public void onCancelled(@NonNull DatabaseError error) {
                if (!closed)
                    denyAccess();
            }
        };
        access.addValueEventListener(accessListener);
    }
    // Lectura: Al revocar acceso detiene sincronización y Workers; conserva el historial Room del teléfono.
    private void denyAccess() {
        authorized = false;
        stopAuthorized();
        androidx.work.WorkManager work = androidx.work.WorkManager.getInstance(context);
        work.cancelUniqueWork("plan-" + scope);
        work.cancelUniqueWork("commands-" + scope);
        connection.postValue(
            "Acceso remoto deshabilitado. El historial Room se conserva en este teléfono");
    }
    // Lectura: Quita listeners de datos y temporizador; conserva el listener de permisos para detectar cambios
    // Lectura: posteriores.
    private void stopAuthorized() {
        timer.removeCallbacks(freshness);
        if (root != null && planListener != null) {
            root.child("plan").removeEventListener(planListener);
            root.child("state").removeEventListener(stateListener);
            root.child("events").removeEventListener(eventsListener);
            root.child("commandResults")
                .child(BuildConfig.COMMAND_MODE)
                .removeEventListener(resultsListener);
            connected.removeEventListener(connectionListener);
            planListener = null;
            stateListener = null;
            eventsListener = null;
            resultsListener = null;
            connectionListener = null;
        }
    }
    // Lectura: Con permiso y vínculo comprobados conecta listeners, cola de planes y cola de comandos.
    private void startAuthorized() {
        // Lectura: Ruta especial del SDK: indica conexión de este cliente, no demuestra que el ESP32 esté en línea.
        connected = FirebaseDatabase.getInstance().getReference(".info/connected");
        connectionListener = listener(s
            -> connection.postValue(Boolean.TRUE.equals(s.getValue(Boolean.class))
                    ? "Firebase conectado · " + BuildConfig.DEVICE_ID
                    : "Sin conexión · historial y borradores en Room"));
        connected.addValueEventListener(connectionListener);
        // Lectura: El callback solo encola el procesamiento; importPlan y SQL se ejecutan en el hilo de disco.
        planListener = listener(s -> task(() -> {
            if (authorized)
                importPlan(s, false);
        }));
        root.child("plan").addValueEventListener(planListener);
        stateListener = listener(s -> {
            lastState = s;
            renderState();
        });
        root.child("state").addValueEventListener(stateListener);
        timer.postDelayed(freshness, 5000);
        eventsListener = new ChildEventListener() {
            public void onChildAdded(@NonNull DataSnapshot s, String previous) {
                ingest(s);
            }
            public void onChildChanged(@NonNull DataSnapshot s, String previous) {
                ingest(s);
            }
            public void onChildRemoved(@NonNull DataSnapshot s) {
            }
            public void onChildMoved(@NonNull DataSnapshot s, String previous) {
            }
            public void onCancelled(@NonNull DatabaseError e) {
                connection.postValue(e.getMessage());
            }
        };
        root.child("events").addChildEventListener(eventsListener);
        // Lectura: Los resultados del dispositivo actualizan la fila existente en Room, conservando el identificador
        // Lectura: del comando.
        resultsListener = listener(s -> task(() -> {
            if (!authorized)
                return;
            for (DataSnapshot result : s.getChildren()) {
                if (result.getKey() != null) dao.commandResult(scope,result.getKey(),
                    String.valueOf(result.child("status").getValue())+" · "+String.valueOf(result.child("reason").getValue()),
                    new JSONObject((Map<?,?>)result.getValue()).toString());
            }
        }));
        root.child("commandResults")
            .child(BuildConfig.COMMAND_MODE)
            .addValueEventListener(resultsListener);
        CommandWorker.enqueue(context, uid);
        SyncWorker.enqueue(context, uid);
    }
    // Lectura: Muestra fase y revisión aplicada; una telemetría de más de treinta segundos se señala como antigua.
    private void renderState() {
        DataSnapshot s = lastState;
        if (s != null) {
            Long time = s.child("updatedAt").getValue(Long.class);
            Long revision = s.child("appliedRevision").getValue(Long.class);
            Boolean sim = s.child("simulation").getValue(Boolean.class);
            String stale =
                time == null || System.currentTimeMillis() - time > 30000 ? " · dato antiguo" : "";
            deviceState.postValue("ESP32 · revisión aplicada " + revision + " · "
                + (Boolean.TRUE.equals(sim) ? "SIMULACIÓN" : "hardware") + stale + "\n"
                + Labels.phase(s.child("phase").getValue(Long.class)) + " · "
                + (Boolean.TRUE.equals(s.child("calibrated").getValue(Boolean.class))
                        ? "calibrado"
                        : "requiere calibración"));
        }
    }
    // Lectura: Convierte un evento Firebase en entidad Room; el ID remoto estable evita duplicados al reconectar.
    private void ingest(DataSnapshot snapshot) {
        try {
            DoseEvent e = snapshot.getValue(DoseEvent.class);
            if (e == null || snapshot.getKey() == null)
                return;
            // Lectura: Asigna el ámbito cuenta:dispositivo antes de insertar; no mezcla historiales de responsables
            // Lectura: distintos.
            e.scope = scope;
            e.eventId = snapshot.getKey();
            task(() -> {
                if (authorized && dao.insertEvent(e) != -1)
                    Alerts.event(context, e);
            });
        } catch (RuntimeException e) {
            connection.postValue("Evento inválido recibido");
        }
    }
    // Conserva el borrador pendiente salvo recarga explícita; valida el plan remoto antes de guardarlo.
    private void importPlan(DataSnapshot s, boolean force) {
        try {
            PlanDraft existing = dao.draft(scope);
            if (!force && existing != null && existing.dirty)
                return;
            if (s.child("doses").exists()
                && !BuildConfig.COMMAND_MODE.equals(s.child("targetMode").getValue(String.class)))
                throw new IllegalStateException(
                    "Plan destinado a otro modo; retira sus horarios antes de cambiar");
            PlanDraft d = new PlanDraft();
            d.scope = scope;
            d.targetMode = BuildConfig.COMMAND_MODE;
            Long revision = s.child("revision").getValue(Long.class);
            d.baseRevision = revision == null ? 0 : revision;
            JSONObject doses = new JSONObject();
            for (DataSnapshot dose : s.child("doses").getChildren()) doses.put(dose.getKey(),new JSONObject(
                    (Map<?,?>)dose.getValue()));
            d.json = doses.toString();
            PlanCodec.doses(d.json);
            d.status = "Plan de Firebase · revisión " + d.baseRevision;
            // Lectura: Persiste este borrador en Room; conserva su estado pendiente o importado al cerrar la app.
            dao.saveDraft(d);
        } catch (Exception e) {
            connection.postValue("Plan remoto inválido: " + e.getMessage());
        }
    }
    // El diálogo de MainActivity pidió sustituir el borrador por la versión remota; force=true lo permite.
    public void reloadRemote() {
        if (root == null || !authorized) {
            connection.setValue(
                "Configura Firebase e inicia sesión con el responsable vinculado para recargar");
            return;
        }
        root.child("plan")
            .get()
            .addOnSuccessListener(s -> task(() -> importPlan(s, true)))
            .addOnFailureListener(
                e -> connection.setValue("No se pudo recargar: " + e.getMessage()));
    }
    // Exige una fecha al menos un minuto futura y crea un ID nuevo solo para esta nueva dosis.
    public void add(long at, int compartment) {
        mutate(json -> {
            if (at < System.currentTimeMillis() + 60000)
                throw new IllegalArgumentException(
                    "Elige una hora al menos un minuto en el futuro");
            JSONObject value = new JSONObject();
            value.put("scheduledAt", at);
            value.put("compartment", compartment);
            json.put(UUID.randomUUID().toString(), value);
        });
    }
    // Edita únicamente el plan: no elimina eventos históricos ni reservas del ESP32.
    public void remove(String id) {
        mutate(json -> json.remove(id));
    }
    interface Edit {
        void apply(JSONObject json) throws Exception;
    }
    // Lectura: Lee, modifica y valida el borrador local en el ejecutor serial; lo guarda antes de pedir sincronización.
    private void mutate(Edit edit) {
        if (uid != null && !authorized) {
            connection.setValue("Espera la comprobación de acceso antes de editar");
            return;
        }
        task(() -> {
            try {
                PlanDraft d = dao.draft(scope);
                if (d == null) {
                    d = new PlanDraft();
                    d.scope = scope;
                    d.targetMode = BuildConfig.COMMAND_MODE;
                }
                if (!d.targetMode.equals(BuildConfig.COMMAND_MODE))
                    throw new IllegalStateException("Recarga Firebase antes de cambiar de modo");
                d.targetMode = BuildConfig.COMMAND_MODE;
                if (d.status.startsWith("Conflicto"))
                    throw new IllegalStateException("Recarga primero el plan de Firebase");
                JSONObject json = new JSONObject(d.json);
                edit.apply(json);
                PlanCodec.doses(json.toString());
                d.json = json.toString();
                // Lectura: Una nueva edición recibe nuevo token; un reintento del mismo borrador conserva su token
                // Lectura: anterior.
                d.token = UUID.randomUUID().toString();
                // Lectura: Marca que existe una edición local pendiente de acuse; estar conectado no equivale a estar
                // Lectura: sincronizado.
                d.dirty = true;
                d.status = uid == null ? "Borrador local de demostración · sin publicar"
                                       : "Pendiente de sincronizar";
                // Lectura: Persiste este borrador en Room; conserva su estado pendiente o importado al cerrar la app.
                dao.saveDraft(d);
                if (uid != null)
                    SyncWorker.enqueue(context, uid);
            } catch (Exception e) {
                connection.postValue(e.getMessage());
            }
        });
    }
    // Lectura: Con sesión autorizada crea una solicitud PING durable; el resultado llegará por otro listener.
    public void ping() {
        if (uid == null || !authorized) {
            connection.setValue(
                "Inicia sesión con el responsable vinculado para comprobar el ESP32");
            return;
        }
        task(() -> {
            try {
                CommandWorker.queue(context, uid, UUID.randomUUID().toString(), "PING", 0);
            } catch (Exception e) {
                connection.postValue("No se pudo guardar el comando");
            }
        });
    }
    // Lectura: Reanuda las dos colas persistentes sin fabricar nuevas dosis ni nuevos IDs de comandos ya guardados.
    public void retry() {
        if (uid != null && authorized) {
            SyncWorker.enqueue(context, uid);
            CommandWorker.enqueue(context, uid);
        }
    }
    // Lectura: Marca el repositorio cerrado, retira callbacks y deja terminar el ejecutor sin borrar la base.
    public boolean isAuthorized() { return uid != null && authorized && !closed; }
    public void close() {
        closed = true;
        authorized = false;
        stopAuthorized();
        if (access != null && accessListener != null)
            access.removeEventListener(accessListener);
        disk.shutdown();
    }
}
