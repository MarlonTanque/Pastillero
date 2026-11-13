package mx.edu.badi.pastillero;

import android.os.Bundle;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.android.gms.tasks.Task;
import com.google.android.gms.tasks.Tasks;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.*;
import org.junit.Test;
import org.junit.Assume;
import java.util.*;
import java.util.concurrent.TimeUnit;
import static org.junit.Assert.*;

/** Prueba real optativa: recibe credenciales al ejecutar, nunca en fuentes ni APK. */
public class FirebaseConnectionTest {
    private static <T> T waitFor(Task<T> task) throws Exception {
        return Tasks.await(task, 25, TimeUnit.SECONDS);
    }
    private static void denied(Task<?> task) throws Exception {
        try {
            waitFor(task);
            fail("Operation unexpectedly allowed");
        } catch (java.util.concurrent.ExecutionException expected) {
            String message =
                String.valueOf(expected.getCause().getMessage()).toLowerCase(Locale.ROOT);
            assertTrue("Expected database permission denial",
                message.contains("permission") && message.contains("denied"));
        }
    }
    @Test
    public void authenticatedSdkRoundTripAndOfflineRetry() throws Exception {
        roundTrip("");
    }
    @Test
    public void versionTwoSdkRoundTripAndOfflineRetry() throws Exception {
        roundTrip("/v2");
    }
    private void roundTrip(String protocolPath) throws Exception {
        Bundle args = InstrumentationRegistry.getArguments();
        Assume.assumeTrue("Live credentials are supplied only by the private integration runner",
            args.getString("liveFirebase", "false").equals("true"));
        assertEquals("pastillerobadi", BuildConfig.FIREBASE_PROJECT_ID);
        List<FirebaseApp> apps = new ArrayList<>();
        List<FirebaseAuth> auths = new ArrayList<>();
        try {
            FirebaseOptions options = new FirebaseOptions.Builder()
                                          .setProjectId(BuildConfig.FIREBASE_PROJECT_ID)
                                          .setApplicationId(BuildConfig.FIREBASE_APP_ID)
                                          .setApiKey(BuildConfig.FIREBASE_API_KEY)
                                          .setDatabaseUrl(BuildConfig.FIREBASE_DATABASE_URL)
                                          .build();
            for (String role : new String[] {"owner", "device", "anonymous"}) {
                FirebaseApp app = FirebaseApp.initializeApp(
                    InstrumentationRegistry.getInstrumentation().getTargetContext(), options,
                    "live-" + role + "-" + UUID.randomUUID());
                apps.add(app);
                FirebaseAuth auth = FirebaseAuth.getInstance(app);
                auths.add(auth);
                if (!role.equals("anonymous"))
                    waitFor(auth.signInWithEmailAndPassword(
                        args.getString(role + "Email"), args.getString(role + "Password")));
            }
            FirebaseDatabase owner = FirebaseDatabase.getInstance(apps.get(0)),
                             device = FirebaseDatabase.getInstance(apps.get(1));
            String path = "devices/" + BuildConfig.DEVICE_ID,
                   uid = auths.get(0).getCurrentUser().getUid();
            assertEquals(
                uid, waitFor(owner.getReference(path + "/ownerUid").get()).getValue(String.class));
            assertEquals(auths.get(1).getCurrentUser().getUid(),
                waitFor(device.getReference(path + "/deviceUid").get()).getValue(String.class));
            assertEquals(Boolean.TRUE,
                waitFor(owner.getReference("access/users/" + uid + "/enabled").get())
                    .getValue(Boolean.class));
            denied(FirebaseDatabase.getInstance(apps.get(2)).getReference(path).get());
            denied(owner.getReference("devices").get());
            denied(owner.getReference("access/users/" + uid + "/enabled").setValue(true));
            // V2 comparte el vínculo del dispositivo, pero conserva colas independientes de V1.
            path += protocolPath;
            String id = "qa-" + UUID.randomUUID().toString().replace("-", "");
            long now = System.currentTimeMillis();
            Map<String, Object> command = new HashMap<>();
            command.put("type", "PING");
            command.put("requestedBy", uid);
            command.put("requestedAt", now);
            command.put("expiresAt", now + 600000);
            command.put("targetMode", "simulation");
            command.put("planRevision", 0L);
            DatabaseReference request = owner.getReference(path + "/commandRequests/" + id);
            owner.goOffline();
            Task<Void> queued = request.setValue(command);
            owner.goOnline();
            waitFor(queued);
            waitFor(request.setValue(command));
            assertEquals("PING",
                waitFor(device.getReference(path + "/commandRequests/" + id + "/type").get())
                    .getValue(String.class));
            denied(device.getReference(path + "/commandRequests/" + id).setValue(command));
            Map<String, Object> result = new HashMap<>();
            result.put("status", "COMPLETED");
            result.put("reason", "OK");
            result.put("requestedAt", now);
            result.put("executedAt", System.currentTimeMillis());
            result.put("planRevision", 0L);
            result.put("simulation", true);
            waitFor(
                device.getReference(path + "/commandResults/simulation/" + id).setValue(result));
            assertEquals("COMPLETED",
                waitFor(
                    owner.getReference(path + "/commandResults/simulation/" + id + "/status").get())
                    .getValue(String.class));
            waitFor(auths.get(0).getCurrentUser().getIdToken(true));
        } finally {
            for (FirebaseAuth auth : auths) auth.signOut();
            for (FirebaseApp app : apps) app.delete();
        }
    }
}
