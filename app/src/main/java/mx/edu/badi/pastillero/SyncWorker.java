package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.*;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.*;
import java.util.*;
import java.util.concurrent.*;

public class SyncWorker extends Worker {
    public SyncWorker(@NonNull Context c, @NonNull WorkerParameters p) {
        super(c, p);
    }
    // Lectura: Construye cuenta:dispositivo; la misma clave se usa en Room y en los nombres de trabajo.
    static String scope(String uid) {
        return uid + ":" + BuildConfig.DEVICE_ID;
    }
    // Lectura: Programa trabajo persistente con conexión requerida y retroceso exponencial; no ejecuta SQL en la
    // Lectura: Activity.
    public static void enqueue(Context c, String uid) {
        Data data = new Data.Builder().putString("uid", uid).build();
        Constraints net =
            new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        WorkManager.getInstance(c).enqueueUniqueWork("plan-" + scope(uid),
            ExistingWorkPolicy.APPEND_OR_REPLACE,
            new OneTimeWorkRequest.Builder(SyncWorker.class)
                .setInputData(data)
                .setConstraints(net)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build());
    }
    @NonNull
    @Override
    // Lectura: WorkManager llama este método en un hilo de trabajo; las esperas de red acotadas no bloquean la
    // Lectura: pantalla.
    public Result doWork() {
        if (!PastilleroApp.cloudReady())
            return Result.success();
        String uid = getInputData().getString("uid");
        if (uid == null || FirebaseAuth.getInstance().getCurrentUser() == null
            || !uid.equals(FirebaseAuth.getInstance().getCurrentUser().getUid()))
            return Result.success();
        PastilleroDao dao = PastilleroDatabase.get(getApplicationContext()).dao();
        PlanDraft draft = dao.draft(scope(uid));
        // Lectura: Sin borrador pendiente no hay nada que publicar; evita incrementar revisiones por una simple
        // Lectura: reconexión.
        if (draft == null || !draft.dirty)
            return Result.success();
        if (!BuildConfig.COMMAND_MODE.equals(draft.targetMode)) {
            dao.status(
                draft.scope, draft.token, "Conflicto: borrador de otro modo; recarga Firebase");
            return Result.failure();
        }
        try {
            Map<String, Object> doses = PlanCodec.doses(draft.json);
            // Lectura: Puente entre callback Firebase y Worker síncrono: espera con límite solo en el hilo de trabajo.
            CountDownLatch done = new CountDownLatch(1);
            boolean[] committed = {false}, already = {false};
            DatabaseError[] failure = {null};
            DatabaseReference ref = FirebaseDatabase.getInstance()
                                        .getReference("devices")
                                        .child(BuildConfig.DEVICE_ID)
                                        .child("plan");
            Transaction.Handler handler = new Transaction.Handler() {
                @NonNull
                // Lectura: Firebase puede repetir este callback si otra escritura compite; por eso compara revisión y
                // Lectura: token.
                public Transaction.Result doTransaction(@NonNull MutableData current) {
                    already[0] = false;
                    Long revision = current.child("revision").getValue(Long.class);
                    long rev = revision == null ? 0 : revision;
                    // El mismo borrador pudo confirmarse antes de un reinicio; su token permite reconocerlo.
                    String token = current.child("token").getValue(String.class);
                    // Lectura: Detecta que el mismo borrador ya llegó antes de perderse el acuse; evita otra revisión y
                    // Lectura: otro envío.
                    if (draft.token.equals(token) && rev == draft.baseRevision + 1) {
                        already[0] = true;
                        return Transaction.abort();
                    }
                    // Lectura: Un plan remoto más reciente produce conflicto; no lo sobrescribe con un borrador
                    // Lectura: atrasado.
                    if (revision != null && rev != draft.baseRevision)
                        return Transaction.abort();
                    Map<String, Object> plan = new HashMap<>();
                    plan.put("revision", draft.baseRevision + 1);
                    plan.put("doses", doses);
                    plan.put("token", draft.token);
                    plan.put("targetMode", BuildConfig.COMMAND_MODE);
                    current.setValue(plan);
                    return Transaction.success(current);
                }
                public void onComplete(
                    DatabaseError error, boolean success, DataSnapshot snapshot) {
                    failure[0] = error;
                    committed[0] = success || already[0];
                    done.countDown();
                }
            };
            // No emitir cambios locales especulativos: Room conserva la cola hasta el acuse remoto.
            // Lectura: Publica con control de concurrencia y sin emitir eventos locales especulativos; espera acuse del
            // Lectura: servidor.
            ref.runTransaction(handler, false);
            // Lectura: Si el acuse tarda más de veinticinco segundos se reintenta con el mismo token.
            if (!done.await(25, TimeUnit.SECONDS))
                return Result.retry();
            if (committed[0]) {
                CommandWorker.queue(getApplicationContext(), uid, draft.token, "APPLY_PLAN",
                    draft.baseRevision + 1);
                // Lectura: Limpia dirty solo si el token sigue siendo el enviado; no confirma por error una edición
                // Lectura: posterior.
                dao.acknowledge(draft.scope, draft.token, draft.baseRevision + 1);
                return Result.success();
            }
            if (failure[0] != null) {
                dao.status(draft.scope, draft.token, "Pendiente: " + failure[0].getMessage());
                return failure[0].getCode() == DatabaseError.PERMISSION_DENIED ? Result.failure()
                                                                               : Result.retry();
            }
            dao.status(draft.scope, draft.token, "Conflicto: recarga Firebase antes de editar");
            return Result.failure();
        } catch (Exception e) {
            dao.status(draft.scope, draft.token, "Error: " + e.getMessage());
            return Result.failure();
        }
    }
}
