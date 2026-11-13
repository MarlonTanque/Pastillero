package mx.edu.badi.pastillero;

import android.app.Activity;
import android.content.Intent;
import android.webkit.WebView;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.webkit.WebViewFeature;
import com.google.firebase.auth.FirebaseAuth;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;

/** Ejecuta el APK real en el AVD de QA: React → puente por origen → Java → Room → React. */
public class DashboardBridgeTest {
    private String eval(WebView web, String js) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<String> out = new AtomicReference<>();
        InstrumentationRegistry.getInstrumentation().runOnMainSync(
            () -> web.evaluateJavascript(js, s -> {
                out.set(s);
                done.countDown();
            }));
        assertTrue("JavaScript no respondió", done.await(10, TimeUnit.SECONDS));
        return out.get();
    }
    private JSONObject call(WebView web, String action, JSONObject payload) throws Exception {
        String id = UUID.randomUUID().toString();
        JSONObject request = new JSONObject()
                                 .put("version", 1)
                                 .put("id", id)
                                 .put("action", action)
                                 .put("payload", payload);
        eval(web,
            "window.__qaReply=null;(()=>{const "
                + "previous=window.BadiNative.onmessage;window.BadiNative.onmessage=e=>{if("
                  + "previous)"
                + "previous(e);const r=JSON.parse(e.data);if(r.id===" + JSONObject.quote(id)
                + ")window.__qaReply=r;};window.BadiNative.postMessage("
                + JSONObject.quote(request.toString()) + ");})()");
        for (int i = 0; i < 100; i++) {
            String value = eval(web, "JSON.stringify(window.__qaReply)");
            if (value != null && !value.equals("null") && !value.equals("\"null\""))
                return new JSONObject(new JSONArray("[" + value + "]").getString(0));
            Thread.sleep(100);
        }
        throw new AssertionError("El puente no devolvió el resultado");
    }
    private Activity launch() throws Exception {
        assertTrue("El WebView del AVD debe soportar mensajes por origen",
            WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER));
        if (PastilleroApp.cloudReady())
            FirebaseAuth.getInstance().signOut();
        Activity activity = InstrumentationRegistry.getInstrumentation().startActivitySync(
            new Intent(InstrumentationRegistry.getInstrumentation().getTargetContext(),
                DashboardActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        WebView web = activity.findViewById(R.id.dashboard_web);
        for (int i = 0; i < 150; i++) {
            if ("\"object\"".equals(eval(web, "typeof window.BadiNative"))
                && "true".equals(eval(web, "!!document.querySelector('h1')")))
                return activity;
            Thread.sleep(100);
        }
        throw new AssertionError("La interfaz React local no terminó de cargar");
    }
    @Test
    public void localHttpsBridgeLoadsReactAndReturnsFiveSpacesWithoutSecrets() throws Exception {
        Activity activity = launch();
        try {
            WebView web = activity.findViewById(R.id.dashboard_web);
            JSONObject reply = call(web, "snapshot", new JSONObject());
            assertTrue(reply.toString(), reply.getBoolean("ok"));
            JSONObject data = reply.getJSONObject("data");
            assertEquals(5, data.getJSONObject("settings").getInt("positions"));
            assertFalse(data.getBoolean("signedIn"));
            assertFalse(reply.toString().contains("password"));
            assertFalse(reply.toString().contains("idToken"));
            assertFalse(reply.toString().contains("apiKey"));
            assertEquals(DashboardActivity.PAGE,
                new JSONArray("[" + eval(web, "location.href") + "]").getString(0));
            android.graphics.Bitmap screenshot =
                InstrumentationRegistry.getInstrumentation().getUiAutomation().takeScreenshot();
            assertNotNull(screenshot);
            try (java.io.FileOutputStream out = new java.io.FileOutputStream(new java.io.File(
                     activity.getExternalFilesDir(null), "dashboard-v2-android.png"))) {
                screenshot.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
            }
        } finally {
            InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
        }
    }
    @Test
    public void reactBridgeWritesRoomAndDeletionPreservesOwnHistory() throws Exception {
        Activity activity = launch();
        String id = UUID.randomUUID().toString(), eventId = "qa-" + UUID.randomUUID().toString();
        String scope = SyncWorker.scope("local");
        PastilleroDatabase db = PastilleroDatabase.get(activity);
        try {
            WebView web = activity.findViewById(R.id.dashboard_web);
            JSONObject medicine = new JSONObject()
                                      .put("id", id)
                                      .put("name", "<img src=x onerror=window.pwned=1>")
                                      .put("mode", "daily")
                                      .put("times", new JSONArray().put("08:00"))
                                      .put("zoneId", "UTC")
                                      .put("compartment", 4)
                                      .put("intervalMinutes", 480)
                                      .put("startAt", System.currentTimeMillis() + 300000)
                                      .put("endAt", 0)
                                      .put("enabled", true);
            assertTrue(call(web, "saveMedication", medicine).getBoolean("ok"));
            assertTrue(
                db.dao().medications(scope).stream().anyMatch(x -> x.medicationId.equals(id)));
            eval(web, "location.hash='/medications'");
            Thread.sleep(200);
            assertEquals("0", eval(web, "document.querySelectorAll('img[src=x]').length"));
            assertEquals("\"undefined\"", eval(web, "typeof window.pwned"));
            DoseEvent event = new DoseEvent();
            event.scope = scope;
            event.eventId = eventId;
            event.medicationId = id;
            event.doseId = id;
            event.type = "CONFIRMED";
            event.simulation = true;
            event.scheduledAt = 1800000000000L;
            event.actualAt = 1800000001000L;
            event.compartment = 4;
            db.dao().insertEvent(event);
            assertTrue(
                call(web, "deleteMedication", new JSONObject().put("id", id)).getBoolean("ok"));
            assertTrue(db.dao().events(scope).stream().anyMatch(x -> x.eventId.equals(eventId)));
            assertFalse(call(web, "DISPENSE", new JSONObject()).getBoolean("ok"));
        } finally {
            db.dao().deleteMedication(scope, id);
            db.getOpenHelper().getWritableDatabase().execSQL(
                "DELETE FROM dose_events WHERE scope=? AND eventId=?",
                new Object[] {scope, eventId});
            InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
        }
    }
    @Test
    public void navigationOutsidePackagedOriginIsRejected() throws Exception {
        assertTrue(DashboardActivity.local(android.net.Uri.parse(DashboardActivity.PAGE)));
        assertFalse(DashboardActivity.local(
            android.net.Uri.parse("https://attacker.invalid/assets/dashboard/index.html")));
        assertFalse(
            DashboardActivity.local(android.net.Uri.parse("file:///android_asset/index.html")));
        assertFalse(DashboardActivity.local(android.net.Uri.parse(
            "https://appassets.androidplatform.net:444/assets/dashboard/index.html")));
        assertFalse(DashboardActivity.local(
            android.net.Uri.parse("https://appassets.androidplatform.net/assets/other.html")));
    }
}
