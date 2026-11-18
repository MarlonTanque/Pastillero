package mx.edu.badi.pastillero;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.webkit.*;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.webkit.*;
import com.google.firebase.auth.FirebaseAuth;
import java.util.Collections;
import org.json.*;

/** Pantalla React local: origen HTTPS fijo, puente de mensajes por origen y navegación cerrada. */
public class DashboardActivity extends AppCompatActivity {
    public static final String PAGE = BridgeProtocol.ORIGIN + "/assets/dashboard/index.html";
    private WebView web;
    private DashboardRepository repo;
    private long weekStart;
    private boolean closed;
    @Override
    public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setContentView(R.layout.activity_dashboard);
        weekStart = saved == null ? 0 : saved.getLong("weekStart");
        web = findViewById(R.id.dashboard_web);
        findViewById(R.id.classic_view)
            .setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            ((TextView) findViewById(R.id.web_error)).setText(R.string.webview_update);
            web.setVisibility(android.view.View.GONE);
            findViewById(R.id.classic_view).setVisibility(android.view.View.VISIBLE);
            return;
        }
        solicitarPermisoNotificaciones();
        repo = new DashboardRepository(this);
        configurarContenidoLocal();
        registrarPuenteSeguro();
        observarDatosLocales();
        configurarBotonAtras();
        web.loadUrl(PAGE);
    }
    // Igual que en las prácticas: onCreate coordina pasos con nombres descriptivos.
    // Cada paso conserva sus comprobaciones de seguridad y su ejecución asíncrona.
    private void solicitarPermisoNotificaciones() {
        if (android.os.Build.VERSION.SDK_INT >= 33
            && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)
                != android.content.pm.PackageManager.PERMISSION_GRANTED
            && !getPreferences(MODE_PRIVATE).getBoolean("notificationAsked", false)) {
            getPreferences(MODE_PRIVATE).edit().putBoolean("notificationAsked", true).apply();
            requestPermissions(new String[] {android.Manifest.permission.POST_NOTIFICATIONS}, 2);
        }
    }
    @SuppressLint("SetJavaScriptEnabled")
    // Solo recursos propios; no hay URLs remotas ni addJavascriptInterface.
    private void configurarContenidoLocal() {
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        WebViewAssetLoader loader =
            new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!local(uri))
                    return new WebResourceResponse("text/plain", "UTF-8", 403, "Forbidden",
                        Collections.emptyMap(), new java.io.ByteArrayInputStream(new byte[0]));
                return loader.shouldInterceptRequest(uri);
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !local(request.getUrl());
            }
            @Override
            public void onReceivedSslError(WebView view, android.webkit.SslErrorHandler handler,
                android.net.http.SslError error) {
                handler.cancel();
            }
        });
    }
    private void registrarPuenteSeguro() {
        if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))
            WebViewCompat.addWebMessageListener(web, "BadiNative",
                Collections.singleton(BridgeProtocol.ORIGIN),
                (view, message, origin, mainFrame, reply) -> {
                    String id = "invalid";
                    try {
                        String text = message.getData();
                        if (text != null && text.length() <= 32768) {
                            Object candidate = new JSONObject(text).opt("id");
                            if (candidate instanceof String
                                && ((String) candidate).matches("[A-Za-z0-9-]{1,64}"))
                                id = (String) candidate;
                        }
                        JSONObject j = BridgeProtocol.parse(text, origin.toString(), mainFrame);
                        id = j.getString("id");
                        String action = j.getString("action");
                        JSONObject payload = j.getJSONObject("payload");
                        final String requestId = id;
                        if (action.equals("snapshot") && payload.has("weekStart"))
                            weekStart = BridgeProtocol.number(payload, "weekStart");
                        if (action.equals("signIn")) {
                            BridgeProtocol.keys(payload);
                            showLogin();
                            sendReply(reply, response(id, true, new JSONObject(), null));
                            return;
                        }
                        if (action.equals("signOut")) {
                            BridgeProtocol.keys(payload);
                            if (PastilleroApp.cloudReady())
                                FirebaseAuth.getInstance().signOut();
                            recreate();
                            return;
                        }
                        if (action.equals("wifiSetup")) {
                            BridgeProtocol.keys(payload);
                            startActivity(new Intent(this, WifiSetupActivity.class));
                            sendReply(reply, response(id, true, new JSONObject(), null));
                            return;
                        }
                        if (action.equals("nativeView")) {
                            BridgeProtocol.keys(payload);
                            startActivity(new Intent(this, MainActivity.class));
                            sendReply(reply, response(id, true, new JSONObject(), null));
                            return;
                        }
                        repo.request(action, payload,
                            data
                            -> runOnUiThread(() -> {
                                if (!closed)
                                    sendReply(reply, response(requestId, true, data, null));
                            }),
                            error -> runOnUiThread(() -> {
                                if (!closed)
                                    sendReply(reply, response(requestId, false, null, error));
                            }));
                    } catch (Exception e) {
                        sendReply(reply,
                            response(id, false, null, "Solicitud no válida o no autorizada"));
                    }
                });
    }
    private void observarDatosLocales() {
        repo.legacy.connection.observe(this, value -> {
            repo.refreshAuthorization();
            pushSnapshot();
        });
        repo.changes.observe(this, value -> pushSnapshot());
        repo.legacy.dao.observeProgram(repo.legacy.scope).observe(this, value -> pushSnapshot());
        repo.legacy.dao.observeEvents(repo.legacy.scope).observe(this, value -> pushSnapshot());
    }
    private void configurarBotonAtras() {
        getOnBackPressedDispatcher().addCallback(
            this, new androidx.activity.OnBackPressedCallback(true) {
                @Override
                public void handleOnBackPressed() {
                    web.evaluateJavascript(
                        "window.__badiBack ? window.__badiBack() : false", result -> {
                            if (!"true".equals(result)) {
                                if (web.canGoBack())
                                    web.goBack();
                                else
                                    finish();
                            }
                        });
                }
            });
    }
    private void sendReply(JavaScriptReplyProxy reply, String message) {
        if (!closed && WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))
            reply.postMessage(message);
    }
    static boolean local(Uri uri) {
        return "https".equals(uri.getScheme())
            && "appassets.androidplatform.net".equals(uri.getHost()) && uri.getPort() == -1
            && uri.getUserInfo() == null && uri.getPath() != null
            && uri.getPath().startsWith("/assets/dashboard/");
    }
    static String response(String id, boolean ok, JSONObject data, String error) {
        try {
            return new JSONObject()
                .put("id", id)
                .put("ok", ok)
                .put("data", data == null ? JSONObject.NULL : data)
                .put("error", error == null ? JSONObject.NULL : error)
                .toString();
        } catch (JSONException e) {
            return "{\"ok\":false,\"error\":\"Respuesta inválida\"}";
        }
    }
    private void pushSnapshot() {
        if (repo == null || closed)
            return;
        JSONObject p = new JSONObject();
        try {
            if (weekStart != 0)
                p.put("weekStart", weekStart);
        } catch (JSONException ignored) {
        }
        repo.request("snapshot", p,
            data
            -> runOnUiThread(() -> {
                if (!closed)
                    web.evaluateJavascript("window.__badiUpdate && window.__badiUpdate("
                            + JSONObject.quote(data.toString()) + ")",
                        null);
            }),
            error -> {});
    }
    private void showLogin() {
        if (!PastilleroApp.cloudReady())
            return;
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        form.setPadding(pad, pad, pad, pad);
        EditText email = new EditText(this);
        email.setHint("Correo del responsable");
        email.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        EditText password = new EditText(this);
        password.setHint("Contraseña de la app");
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        form.addView(email);
        form.addView(password);
        AlertDialog dialog = new AlertDialog.Builder(this)
                                 .setTitle("Entrar a Pastillero Badi")
                                 .setView(form)
                                 .setNegativeButton("Cancelar", null)
                                 .setPositiveButton("Entrar", null)
                                 .create();
        dialog.setOnShowListener(
            x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                String account = email.getText().toString().trim(),
                       secret = password.getText().toString();
                if (account.isEmpty() || secret.isEmpty()) {
                    email.setError("Introduce tu cuenta de la app");
                    return;
                }
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                FirebaseAuth.getInstance()
                    .signInWithEmailAndPassword(account, secret)
                    .addOnCompleteListener(task -> {
                        password.setText("");
                        if (task.isSuccessful()) {
                            dialog.dismiss();
                            recreate();
                        } else {
                            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                            email.setError("No se pudo iniciar sesión");
                        }
                    });
            }));
        dialog.show();
    }
    @Override
    protected void onSaveInstanceState(Bundle out) {
        out.putLong("weekStart", weekStart);
        super.onSaveInstanceState(out);
    }
    @Override
    protected void onDestroy() {
        closed = true;
        if (repo != null)
            repo.close();
        if (web != null) {
            web.stopLoading();
            web.removeAllViews();
            web.destroy();
        }
        super.onDestroy();
    }
}
