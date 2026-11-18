package mx.edu.badi.pastillero;
import com.espressif.provisioning.SecureCapabilities;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class WifiSetupPolicyTest {
    private static final String CODE = "0123456789abcdef01234567";
    private static void invalid(Runnable action) {
        try { action.run(); fail("Debe rechazarse"); } catch (IllegalArgumentException expected) { }
    }
    @Test public void ssidPreservesSpacesAndUnicode() { WifiSetupPolicy.network(" Mi red ñ ", "clave-ficticia", false); }
    @Test public void ssidLimitCountsBytes() {
        WifiSetupPolicy.network("ñ".repeat(16), "clave-ficticia", false);
        invalid(() -> WifiSetupPolicy.network("ñ".repeat(17), "clave-ficticia", false));
    }
    @Test public void invalidSsidsRejected() {
        for (String ssid : new String[] {"", "a\u0000b", "red\n", "x".repeat(33)}) invalid(() -> WifiSetupPolicy.network(ssid, "clave-ficticia", false));
    }
    @Test public void passwordLimitsAndHexKey() {
        WifiSetupPolicy.network("red", "a".repeat(63), false);
        WifiSetupPolicy.network("red", "a".repeat(64), false);
        for (String value : new String[] {"corta", "z".repeat(64), "a".repeat(65), "clave\n123"}) invalid(() -> WifiSetupPolicy.network("red", value, false));
    }
    @Test public void openNetworkRequiresExplicitChoice() {
        WifiSetupPolicy.network("red", "", true);
        invalid(() -> WifiSetupPolicy.network("red", "", false));
        invalid(() -> WifiSetupPolicy.network("red", "con-clave", true));
    }
    @Test public void deviceHasIndividualCode() { WifiSetupPolicy.device("BADI_SETUP_ABC123", CODE); }
    @Test public void invalidDevicesRejected() {
        invalid(() -> WifiSetupPolicy.device("otra-red", CODE));
        invalid(() -> WifiSetupPolicy.device("BADI_SETUP_ABC123", "abcd1234"));
    }
    @Test public void securityOneAccepted() throws Exception {
        SecureCapabilities.requireSecurity1("{\"prov\":{\"sec_ver\":1,\"cap\":[]}}", CODE);
    }
    @Test public void downgradeAndMissingProofFailClosed() throws Exception {
        for (String json : new String[] {"{\"prov\":{\"sec_ver\":0}}", "{\"prov\":{}}", "{\"prov\":{\"sec_ver\":1,\"cap\":[\"no_pop\"]}}"}) {
            try { SecureCapabilities.requireSecurity1(json, CODE); fail("No debe degradar seguridad"); } catch (SecurityException expected) { }
        }
    }
    @Test public void wifiBridgeDoesNotAcceptCredentials() throws Exception {
        JSONObject request = BridgeProtocol.parse("{\"version\":1,\"id\":\"wifi-1\",\"action\":\"wifiSetup\",\"payload\":{}}", BridgeProtocol.ORIGIN, true);
        BridgeProtocol.keys(request.getJSONObject("payload"));
        JSONObject withSecret = new JSONObject().put("password", "ficticia");
        invalid(() -> BridgeProtocol.keys(withSecret));
    }
}
