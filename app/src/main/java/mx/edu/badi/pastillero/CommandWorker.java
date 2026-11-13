package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.*;
import com.google.android.gms.tasks.Tasks;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.*;
import org.json.JSONObject;
import java.util.*;
import java.util.concurrent.TimeUnit;

/** Room conserva la cola; los reintentos mantienen la misma clave y el mismo contenido. */
public class CommandWorker extends Worker {
    public CommandWorker(@NonNull Context c, @NonNull WorkerParameters p) {
        super(c, p);
    }
    public static void queue(Context c, String uid, String id, String type, long revision)
        throws Exception {
        queueForProtocol(c, uid, id, type, revision, 1);
    }
    public static void queueV2(Context c, String uid, String id, String type, long revision)
        throws Exception {
        queueForProtocol(c, uid, id, type, revision, 2);
    }
    private static void queueForProtocol(Context c, String uid, String id, String type,
        long revision, int protocol) throws Exception {
        PastilleroDao dao = PastilleroDatabase.get(c).dao();
        CommandRequest item = new CommandRequest();
        item.scope = SyncWorker.scope(uid);
        item.commandId = id;
        item.protocolVersion = protocol;
        // Lectura: Fija una vez la fecha de creación; reintentar la fila no renueva su vigencia.
        item.createdAt = System.currentTimeMillis();
        JSONObject j = new JSONObject();
        j.put("type", type);
        j.put("requestedBy", uid);
        j.put("requestedAt", item.createdAt);
        // Lectura: Caducidad de diez minutos a partir de la creación original, coherente con
        // firmware y reglas.
        j.put("expiresAt", item.createdAt + 600000);
        j.put("targetMode", protocol == 2 ? "simulation" : BuildConfig.COMMAND_MODE);
        j.put("planRevision", revision);
        item.json = j.toString();
        // Lectura: IGNORE preserva la primera solicitud con ese ID; los reintentos no sustituyen su
        // contenido.
        dao.insertCommand(item);
        enqueue(c, uid);
    }
    // Lectura: Programa trabajo persistente con conexión requerida y retroceso exponencial; no
    // ejecuta SQL en la Lectura: Activity.
    public static void enqueue(Context c, String uid) {
        WorkManager.getInstance(c).enqueueUniqueWork("commands-" + SyncWorker.scope(uid),
            ExistingWorkPolicy.APPEND_OR_REPLACE,
            new OneTimeWorkRequest.Builder(CommandWorker.class)
                .setInputData(new Data.Builder().putString("uid", uid).build())
                .setConstraints(
                    new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build());
    }
    @NonNull
    @Override
    // Lectura: WorkManager llama este método en un hilo de trabajo; las esperas de red acotadas no
    // bloquean la Lectura: pantalla.
    public Result doWork() {
        if (!PastilleroApp.cloudReady())
            return Result.success();
        String uid = getInputData().getString("uid");
        if (uid == null || FirebaseAuth.getInstance().getCurrentUser() == null
            || !uid.equals(FirebaseAuth.getInstance().getCurrentUser().getUid()))
            return Result.success();
        PastilleroDao dao = PastilleroDatabase.get(getApplicationContext()).dao();
        for (CommandRequest item : dao.pendingCommands(SyncWorker.scope(uid))) {
            try {
                JSONObject json = new JSONObject(item.json);
                // Una escritura sin acuse pudo llegar al servidor: comprobarla antes de declararla
                // caducada.
                DatabaseReference base =
                    FirebaseDatabase.getInstance().getReference("devices").child(
                        BuildConfig.DEVICE_ID);
                if (item.protocolVersion == 2)
                    base = base.child("v2");
                else if (item.protocolVersion != 1)
                    throw new IllegalArgumentException("Protocolo desconocido");
                DatabaseReference ref = base.child("commandRequests").child(item.commandId);
                DataSnapshot existing = Tasks.await(ref.get(), 20, TimeUnit.SECONDS);
                if (existing.exists()) {
                    Map<String, Object> payload = payload(json);
                    // Lectura: El mismo ID con otro contenido es conflicto; no se reutiliza para
                    // una orden distinta.
                    if (!payload.equals(existing.getValue())) {
                        dao.commandStatus(
                            item.scope, item.commandId, "Conflicto de identificador", true);
                        continue;
                    }
                } else {
                    if (json.getLong("expiresAt") <= System.currentTimeMillis()) {
                        dao.commandStatus(item.scope, item.commandId, "Caducado sin enviar", true);
                        continue;
                    }
                    // Lectura: Espera como máximo veinte segundos en el Worker; un fallo conserva
                    // la fila para Lectura: reintentar.
                    Tasks.await(ref.setValue(payload(json)), 20, TimeUnit.SECONDS);
                }
                dao.commandStatus(
                    item.scope, item.commandId, "Enviado · esperando respuesta", true);
            } catch (Exception e) {
                return Result.retry();
            }
        }
        return Result.success();
    }
    // Lectura: Entrega solo los seis campos públicos del contrato; no transmite contraseñas ni
    // campos internos Room.
    private static Map<String, Object> payload(JSONObject j) throws Exception {
        Map<String, Object> map = new HashMap<>();
        map.put("type", j.getString("type"));
        map.put("requestedBy", j.getString("requestedBy"));
        map.put("targetMode", j.getString("targetMode"));
        map.put("planRevision", j.getLong("planRevision"));
        map.put("requestedAt", j.getLong("requestedAt"));
        map.put("expiresAt", j.getLong("expiresAt"));
        return map;
    }
}
