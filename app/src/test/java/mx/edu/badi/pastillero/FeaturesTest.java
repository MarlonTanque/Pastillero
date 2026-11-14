package mx.edu.badi.pastillero;
import java.util.*;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class FeaturesTest {
    @Test
    public void missingNodeAllowsEverything() throws Exception {
        Map<String, Boolean> f = Features.parse(null);
        for (String name : Features.ALL) assertTrue(Features.allowed(f, name));
    }
    @Test
    public void onlyExplicitFalseBlocks() {
        Map<String, Object> raw = new HashMap<>();
        raw.put("medications", false);
        raw.put("publish", "false");
        raw.put("deviceSettings", true);
        raw.put("unknown", false);
        Map<String, Boolean> f = Features.parse(raw);
        assertFalse(Features.allowed(f, Features.MEDICATIONS));
        assertTrue(Features.allowed(f, Features.PUBLISH));
        assertTrue(Features.allowed(f, Features.DEVICE_SETTINGS));
        assertEquals(1, f.size());
    }
    @Test
    public void mapsBridgeActions() {
        assertEquals(Features.MEDICATIONS, Features.forAction("saveMedication"));
        assertEquals(Features.MEDICATIONS, Features.forAction("deleteMedication"));
        assertEquals(Features.PUBLISH, Features.forAction("publish"));
        assertEquals(Features.PUBLISH, Features.forAction("rebase"));
        assertEquals(Features.DEVICE_SETTINGS, Features.forAction("savePreferences"));
        assertEquals(Features.DIAGNOSTICS, Features.forAction("ping"));
        assertEquals(Features.DIAGNOSTICS, Features.forAction("nativeView"));
        // Consultar, iniciar y cerrar sesión nunca se bloquean.
        assertNull(Features.forAction("snapshot"));
        assertNull(Features.forAction("signOut"));
        assertTrue(Features.allowed(Features.parse(Collections.singletonMap("publish", false)), null));
    }
    @Test
    public void jsonListsEveryFeature() throws Exception {
        JSONObject j = Features.json(Features.parse(Collections.singletonMap("diagnostics", false)));
        assertEquals(4, j.length());
        assertFalse(j.getBoolean("diagnostics"));
        assertTrue(j.getBoolean("medications"));
    }
}
