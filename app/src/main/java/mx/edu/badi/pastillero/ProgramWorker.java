package mx.edu.badi.pastillero;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.*;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.*;
import java.util.*;
import java.util.concurrent.*;
import org.json.*;

/** Publica únicamente v2/program; el firmware 1.5 no consulta esta ruta. */
public class ProgramWorker extends Worker {
    public ProgramWorker(@NonNull Context c, @NonNull WorkerParameters p) {
        super(c, p);
    }
    public static void enqueue(Context c, String uid) {
        WorkManager.getInstance(c).enqueueUniqueWork("program-v2-" + SyncWorker.scope(uid),
            ExistingWorkPolicy.APPEND_OR_REPLACE,
            new OneTimeWorkRequest.Builder(ProgramWorker.class)
                .setInputData(new Data.Builder().putString("uid", uid).build())
                .setConstraints(
                    new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build());
    }
    @NonNull
    @Override
    public Result doWork() {
        String uid = getInputData().getString("uid");
        if (!PastilleroApp.cloudReady() || uid == null
            || FirebaseAuth.getInstance().getCurrentUser() == null
            || !uid.equals(FirebaseAuth.getInstance().getCurrentUser().getUid()))
            return Result.success();
        PastilleroDao dao = PastilleroDatabase.get(getApplicationContext()).dao();
        ProgramOutbox item = dao.program(SyncWorker.scope(uid));
        if (item == null || !item.dirty)
            return Result.success();
        try {
            JSONObject json = new JSONObject(item.json);
            if (json.optInt("version") != 2 || !"simulation".equals(json.optString("targetMode")))
                throw new IllegalArgumentException("Esta entrega publica solo simulación V2");
            Map<String, Object> payload = map(json);
            CountDownLatch done = new CountDownLatch(1);
            boolean[] committed = {false}, already = {false};
            DatabaseError[] failure = {null};
            FirebaseDatabase.getInstance()
                .getReference("devices")
                .child(BuildConfig.DEVICE_ID)
                .child("v2/program")
                .runTransaction(new Transaction.Handler() {
                    @NonNull
                    public Transaction.Result doTransaction(@NonNull MutableData current) {
                        Long revision = current.child("revision").getValue(Long.class);
                        long rev = revision == null ? 0 : revision;
                        already[0] =
                            item.token.equals(current.child("token").getValue(String.class))
                            && rev == item.baseRevision + 1;
                        if (already[0] || (revision != null && rev != item.baseRevision))
                            return Transaction.abort();
                        Map<String, Object> next = new HashMap<>(payload);
                        next.put("revision", item.baseRevision + 1);
                        next.put("token", item.token);
                        current.setValue(next);
                        return Transaction.success(current);
                    }
                    public void onComplete(
                        DatabaseError e, boolean success, DataSnapshot snapshot) {
                        failure[0] = e;
                        committed[0] = success || already[0];
                        done.countDown();
                    }
                }, false);
            if (!done.await(25, TimeUnit.SECONDS))
                return Result.retry();
            if (committed[0]) {
                CommandWorker.queueV2(
                    getApplicationContext(), uid, item.token, "APPLY_PLAN", item.baseRevision + 1);
                dao.acknowledgeProgram(item.scope, item.token, item.baseRevision + 1);
                return Result.success();
            }
            if (failure[0] != null) {
                dao.programStatus(item.scope, item.token, "Pendiente: " + failure[0].getMessage());
                return failure[0].getCode() == DatabaseError.PERMISSION_DENIED ? Result.failure()
                                                                               : Result.retry();
            }
            dao.programStatus(
                item.scope, item.token, "Conflicto: existe una revisión remota más reciente");
            return Result.failure();
        } catch (Exception e) {
            dao.programStatus(item.scope, item.token, "Error al publicar: " + e.getMessage());
            return Result.failure();
        }
    }
    static Map<String, Object> map(JSONObject j) throws JSONException {
        Map<String, Object> out = new HashMap<>();
        Iterator<String> it = j.keys();
        while (it.hasNext()) {
            String k = it.next();
            Object v = j.get(k);
            out.put(k, convert(v));
        }
        return out;
    }
    private static Object convert(Object x) throws JSONException {
        if (x instanceof JSONObject)
            return map((JSONObject) x);
        if (x instanceof JSONArray) {
            List<Object> l = new ArrayList<>();
            JSONArray a = (JSONArray) x;
            for (int i = 0; i < a.length(); i++)
                l.add(convert(a.get(i)));
            return l;
        }
        return x == JSONObject.NULL ? null : x;
    }
}
