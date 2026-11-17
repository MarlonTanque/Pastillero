package mx.edu.badi.pastillero;

import java.util.*;
import org.json.*;

/**
 * Funcionalidades que el dashboard administrativo puede bloquear por cuenta.
 * Se leen de access/users/UID/features; solo el backend escribe ese nodo.
 * Una clave ausente equivale a permitida para conservar el comportamiento previo.
 */
public final class Features {
    public static final String MEDICATIONS = "medications";
    public static final String PUBLISH = "publish";
    public static final String DEVICE_SETTINGS = "deviceSettings";
    public static final String DIAGNOSTICS = "diagnostics";
    public static final List<String> ALL =
        Collections.unmodifiableList(Arrays.asList(MEDICATIONS, PUBLISH, DEVICE_SETTINGS, DIAGNOSTICS));
    public static final String BLOCKED = "Función deshabilitada por el administrador";
    private Features() {
    }
    // Acción del puente React → funcionalidad que la controla; null si no está sujeta a bloqueo.
    public static String forAction(String action) {
        switch (action) {
            case "saveMedication":
            case "deleteMedication":
                return MEDICATIONS;
            case "publish":
            case "retry":
            case "reload":
            case "rebase":
                return PUBLISH;
            case "savePreferences":
                return DEVICE_SETTINGS;
            case "ping":
            case "nativeView":
                return DIAGNOSTICS;
            default:
                return null;
        }
    }
    // Solo un false explícito bloquea; cualquier otro valor conserva el acceso.
    public static Map<String, Boolean> parse(Map<?, ?> raw) {
        Map<String, Boolean> out = new HashMap<>();
        if (raw == null)
            return out;
        for (String name : ALL)
            if (Boolean.FALSE.equals(raw.get(name)))
                out.put(name, false);
        return Collections.unmodifiableMap(out);
    }
    public static boolean allowed(Map<String, Boolean> features, String name) {
        return name == null || !Boolean.FALSE.equals(features.get(name));
    }
    public static JSONObject json(Map<String, Boolean> features) throws JSONException {
        JSONObject j = new JSONObject();
        for (String name : ALL) j.put(name, allowed(features, name));
        return j;
    }
}
