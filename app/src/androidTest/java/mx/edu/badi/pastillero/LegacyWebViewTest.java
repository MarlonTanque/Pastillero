package mx.edu.badi.pastillero;
import android.app.Activity;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.webkit.WebViewFeature;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Perfil API24 original: verifica el cierre seguro de React cuando el proveedor es demasiado
 * antiguo.
 */
public class LegacyWebViewTest {
    @Test
    public void unsupportedProviderOffersNativeViewWithoutUnsafeBridge() {
        assertFalse(WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER));
        Activity a = InstrumentationRegistry.getInstrumentation().startActivitySync(
            new Intent(InstrumentationRegistry.getInstrumentation().getTargetContext(),
                DashboardActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try {
            assertEquals(View.GONE, a.findViewById(R.id.dashboard_web).getVisibility());
            assertTrue(((TextView) a.findViewById(R.id.web_error))
                    .getText()
                    .toString()
                    .contains("WebView"));
            assertEquals(View.VISIBLE, a.findViewById(R.id.classic_view).getVisibility());
        } finally {
            InstrumentationRegistry.getInstrumentation().runOnMainSync(a::finish);
        }
    }
}
