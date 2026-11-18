package mx.edu.badi.pastillero;

import android.widget.*;
import android.view.WindowManager;
import androidx.test.core.app.ActivityScenario;
import org.junit.Test;
import static org.junit.Assert.*;

/** No abre sockets ni cambia redes: formulario y ciclo de vida con credenciales ficticias. */
public class WifiSetupActivityTest {
    @Test public void secretsAreNotRestoredAfterRecreation() {
        try (ActivityScenario<WifiSetupActivity> screen = ActivityScenario.launch(WifiSetupActivity.class)) {
            screen.onActivity(activity -> {
                ((EditText) activity.findViewById(R.id.wifi_code)).setText("0123456789abcdef01234567");
                ((EditText) activity.findViewById(R.id.wifi_password)).setText("Ficticia123");
                assertNotEquals(0, activity.getWindow().getAttributes().flags & WindowManager.LayoutParams.FLAG_SECURE);
            });
            screen.recreate();
            screen.onActivity(activity -> {
                assertEquals("", ((EditText) activity.findViewById(R.id.wifi_code)).getText().toString());
                assertEquals("", ((EditText) activity.findViewById(R.id.wifi_password)).getText().toString());
                assertFalse(activity.findViewById(R.id.wifi_send).isEnabled());
            });
        }
    }
    @Test public void invalidDeviceDoesNotRequestNetworkAndOpenWifiIsExplicit() {
        try (ActivityScenario<WifiSetupActivity> screen = ActivityScenario.launch(WifiSetupActivity.class)) {
            screen.onActivity(activity -> {
                activity.findViewById(R.id.wifi_connect).performClick();
                assertTrue(((TextView) activity.findViewById(R.id.wifi_status)).getText().toString().contains("BADI_SETUP_"));
                assertFalse(activity.findViewById(R.id.wifi_send).isEnabled());
                EditText password = activity.findViewById(R.id.wifi_password);
                password.setText("Ficticia123");
                ((CheckBox) activity.findViewById(R.id.wifi_open)).setChecked(true);
                assertEquals("", password.getText().toString());
                assertFalse(password.isEnabled());
            });
        }
    }
}
