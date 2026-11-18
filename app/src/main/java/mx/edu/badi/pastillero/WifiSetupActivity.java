package mx.edu.badi.pastillero;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.wifi.WifiManager;
import android.os.*;
import android.view.WindowManager;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.espressif.provisioning.*;
import com.espressif.provisioning.listeners.*;
import java.util.ArrayList;
import java.util.concurrent.*;
import org.greenrobot.eventbus.*;

/** Pantalla nativa: las contraseñas no cruzan el puente React, Room ni Firebase. */
public class WifiSetupActivity extends AppCompatActivity {
    private EditText deviceName, code, ssid, password;
    private TextView status;
    private CheckBox open;
    private Button connect, scan, send;
    private ESPDevice device;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler timer = new Handler(Looper.getMainLooper());
    private boolean closed, connected, sending;
    private final Runnable timeout = () -> fail("Se agotó la espera. Vuelve a activar el modo Wi-Fi del pastillero y reintenta.");

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        setContentView(R.layout.activity_wifi_setup);
        deviceName = findViewById(R.id.wifi_device); code = findViewById(R.id.wifi_code);
        ssid = findViewById(R.id.wifi_ssid); password = findViewById(R.id.wifi_password);
        status = findViewById(R.id.wifi_status); open = findViewById(R.id.wifi_open);
        connect = findViewById(R.id.wifi_connect); scan = findViewById(R.id.wifi_scan);
        send = findViewById(R.id.wifi_send);
        EventBus.getDefault().register(this);
        connect.setOnClickListener(v -> connect());
        scan.setOnClickListener(v -> scan());
        send.setOnClickListener(v -> provision());
        open.setOnCheckedChangeListener((button, checked) -> { if (checked) password.setText(""); password.setEnabled(!checked); });
        findViewById(R.id.wifi_close).setOnClickListener(v -> finish());
    }
    private String permission() {
        return Build.VERSION.SDK_INT >= 33 ? Manifest.permission.NEARBY_WIFI_DEVICES : Manifest.permission.ACCESS_FINE_LOCATION;
    }
    private void connect() {
        try { WifiSetupPolicy.device(deviceName.getText().toString().trim(), code.getText().toString().trim()); }
        catch (IllegalArgumentException invalid) { status.setText(invalid.getMessage()); return; }
        if (Build.HARDWARE.contains("ranchu") || Build.HARDWARE.contains("goldfish")) {
            status.setText(R.string.wifi_phone_required);
            return;
        }
        if (checkSelfPermission(permission()) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(Build.VERSION.SDK_INT >= 33 ? new String[] {permission()} : new String[] {Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, 31);
            status.setText(R.string.wifi_message_1);
            return;
        }
        WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(WIFI_SERVICE);
        if (wifi == null || !wifi.isWifiEnabled()) { status.setText(R.string.wifi_message_2); return; }
        disconnect();
        device = new ESPDevice(this, ESPConstants.TransportType.TRANSPORT_SOFTAP, ESPConstants.SecurityType.SECURITY_1);
        device.setProofOfPossession(code.getText().toString().trim());
        connect.setEnabled(false);
        status.setText(R.string.wifi_message_3);
        timer.postDelayed(timeout, 90000);
        try { device.connectWiFiDevice(deviceName.getText().toString().trim(), code.getText().toString().trim()); }
        catch (Exception unavailable) { fail("No se pudo solicitar la conexión local. Revisa Wi-Fi y permisos."); }
    }
    @Subscribe(threadMode = ThreadMode.MAIN)
    public void deviceEvent(DeviceConnectionEvent event) {
        if (closed || device == null) return;
        if (event.getEventType() == ESPConstants.EVENT_DEVICE_CONNECTED) {
            ESPDevice current = device;
            // Validar también antes de escanear; el SDK parcheado vuelve a comprobar Security1.
            io.execute(() -> current.initSession(new ResponseListener() {
                public void onSuccess(byte[] data) { ui(() -> { if (device != current) return; timer.removeCallbacks(timeout); connected = true; scan.setEnabled(true); send.setEnabled(true); code.setText(""); status.setText(R.string.wifi_message_4); }); }
                public void onFailure(Exception error) { ui(() -> fail("Código incorrecto o dispositivo sin aprovisionamiento seguro. No se enviaron datos de tu router.")); }
            }));
        } else if (event.getEventType() == ESPConstants.EVENT_DEVICE_CONNECTION_FAILED) {
            fail("No se encontró el pastillero. Activa su modo Wi-Fi y revisa nombre y código.");
        } else if (!sending && event.getEventType() == ESPConstants.EVENT_DEVICE_DISCONNECTED) {
            fail("Se perdió la conexión local. Reintenta con el pastillero cerca.");
        }
    }
    private void scan() {
        if (!connected || device == null || sending) return;
        ESPDevice current = device;
        scan.setEnabled(false); status.setText(R.string.wifi_message_5);
        io.execute(() -> current.scanNetworks(new WiFiScanListener() {
            public void onWifiListReceived(ArrayList<WiFiAccessPoint> networks) { ui(() -> {
                if (device != current) return;
                scan.setEnabled(true);
                String[] names = networks.stream().map(WiFiAccessPoint::getWifiName).distinct().toArray(String[]::new);
                if (names.length == 0) { status.setText(R.string.wifi_message_6); return; }
                new android.app.AlertDialog.Builder(WifiSetupActivity.this).setTitle("Redes del ESP32")
                    .setItems(names, (dialog, which) -> ssid.setText(names[which])).show();
                status.setText(R.string.wifi_message_7);
            }); }
            public void onWiFiScanFailed(Exception error) { ui(() -> { scan.setEnabled(true); status.setText(R.string.wifi_message_8); }); }
        }));
    }
    private void provision() {
        if (!connected || device == null || sending) return;
        final String network = ssid.getText().toString(), secret = password.getText().toString();
        try { WifiSetupPolicy.network(network, secret, open.isChecked()); }
        catch (IllegalArgumentException invalid) { status.setText(invalid.getMessage()); return; }
        ESPDevice current = device;
        sending = true; send.setEnabled(false); scan.setEnabled(false); open.setEnabled(false);
        password.setText("");
        status.setText(R.string.wifi_message_9);
        timer.postDelayed(timeout, 90000);
        io.execute(() -> current.provision(network, secret, new ProvisionListener() {
            public void createSessionFailed(Exception e) { problem("No se pudo autenticar el dispositivo."); }
            public void wifiConfigSent() { ui(() -> status.setText(R.string.wifi_message_10)); }
            public void wifiConfigFailed(Exception e) { problem("No se pudieron enviar los datos de red."); }
            public void wifiConfigApplied() { ui(() -> status.setText(R.string.wifi_message_11)); }
            public void wifiConfigApplyFailed(Exception e) { problem("El ESP32 no pudo aplicar la red."); }
            public void provisioningFailedFromDevice(ESPConstants.ProvisionFailureReason reason) { problem(reason == ESPConstants.ProvisionFailureReason.AUTH_FAILED ? "La contraseña de red fue rechazada." : reason == ESPConstants.ProvisionFailureReason.NETWORK_NOT_FOUND ? "El ESP32 no encuentra esa red de 2.4 GHz." : "No se pudo conectar a la red. Reintenta."); }
            public void onProvisioningFailed(Exception e) { problem("No se pudo confirmar la conexión. Revisa el dispositivo antes de reintentar."); }
            public void deviceProvisioningSuccess() { ui(() -> {
                timer.removeCallbacks(timeout); sending = false; disconnect(); connect.setEnabled(true); open.setEnabled(true);
                status.setText(R.string.wifi_message_12);
            }); }
            private void problem(String message) { ui(() -> fail(message)); }
        }));
    }
    private void ui(Runnable action) { runOnUiThread(() -> { if (!closed) action.run(); }); }
    private void fail(String message) {
        if (closed) return;
        timer.removeCallbacks(timeout); sending = false; disconnect(); connect.setEnabled(true); open.setEnabled(true);
        password.setText(""); code.setText(""); status.setText(getString(R.string.wifi_recovery_status, message));
    }
    private void disconnect() {
        connected = false; scan.setEnabled(false); send.setEnabled(false);
        ESPDevice previous = device; device = null;
        if (previous != null) { previous.setProofOfPossession(""); previous.disconnectDevice(); }
    }
    @Override protected void onDestroy() {
        closed = true; timer.removeCallbacksAndMessages(null); disconnect();
        password.setText(""); code.setText(""); EventBus.getDefault().unregister(this); io.shutdownNow();
        super.onDestroy();
    }
}
