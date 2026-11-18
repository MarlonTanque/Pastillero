package mx.edu.badi.pastillero;

import java.util.*;
import org.json.*;

/**
 * Superficie mínima del puente: JSON acotado y acciones explícitas, sin evaluar código recibido.
 */
public final class BridgeProtocol {
    public static final String ORIGIN = "https://appassets.androidplatform.net";
    private static final Set<String> ACTIONS = new HashSet<>(
        Arrays.asList("snapshot", "saveMedication", "deleteMedication", "savePreferences",
            "publish", "retry", "reload", "rebase", "ping", "signIn", "signOut", "nativeView", "wifiSetup"));
    private BridgeProtocol() {
    }
    public static JSONObject parse(String text, String origin, boolean mainFrame)
        throws JSONException {
        if (!mainFrame || !ORIGIN.equals(origin))
            throw new SecurityException("Origen no autorizado");
        if (text == null || text.length() > 32768)
            throw new IllegalArgumentException("Mensaje demasiado grande");
        JSONObject j = new JSONObject(text);
        keys(j, "version", "id", "action", "payload");
        if (number(j, "version") != 1 || !string(j, "id").matches("[A-Za-z0-9-]{1,64}")
            || !ACTIONS.contains(string(j, "action")))
            throw new IllegalArgumentException("Mensaje no admitido");
        if (!(j.get("payload") instanceof JSONObject))
            throw new IllegalArgumentException("Falta payload");
        return j;
    }
    public static void keys(JSONObject j, String... names) {
        Set<String> allowed = new HashSet<>(Arrays.asList(names));
        Iterator<String> it = j.keys();
        while (it.hasNext())
            if (!allowed.contains(it.next()))
                throw new IllegalArgumentException("Campo no admitido");
    }
    public static long number(JSONObject j, String key) throws JSONException {
        Object x = j.get(key);
        if (!(x instanceof Number))
            throw new IllegalArgumentException("Número requerido: " + key);
        double d = ((Number) x).doubleValue();
        long n = ((Number) x).longValue();
        if (!Double.isFinite(d) || d != n)
            throw new IllegalArgumentException("Entero requerido: " + key);
        return n;
    }
    public static boolean bool(JSONObject j, String key) throws JSONException {
        Object x = j.get(key);
        if (!(x instanceof Boolean))
            throw new IllegalArgumentException("Booleano requerido");
        return (Boolean) x;
    }
    public static String string(JSONObject j, String key) throws JSONException {
        Object x = j.get(key);
        if (!(x instanceof String))
            throw new IllegalArgumentException("Texto requerido");
        return (String) x;
    }
    public static Medication medication(JSONObject j, String scope, int positions)
        throws JSONException {
        keys(j, "id", "name", "mode", "times", "zoneId", "compartment", "intervalMinutes",
            "startAt", "endAt", "enabled");
        Medication m = new Medication();
        m.scope = scope;
        m.medicationId = string(j, "id");
        m.name = string(j, "name").trim();
        m.mode = string(j, "mode");
        m.timesJson = j.getJSONArray("times").toString();
        m.zoneId = string(j, "zoneId");
        long slot = number(j, "compartment"), interval = number(j, "intervalMinutes");
        if (slot < 1 || slot >= positions || interval < 15 || interval > 10080)
            throw new IllegalArgumentException("Compartimento o intervalo inválido");
        m.compartment = (int) slot;
        m.intervalMinutes = (int) interval;
        m.startAt = number(j, "startAt");
        m.endAt = number(j, "endAt");
        m.enabled = bool(j, "enabled");
        ScheduleEngine.validate(m, positions);
        return m;
    }
    public static DevicePreferences preferences(JSONObject j, String scope) throws JSONException {
        keys(j, "positions", "horizonDays", "pumpDurationMs", "ledEnabled", "buzzerEnabled",
            "lcdEnabled", "exitSensorEnabled", "servoEnabled", "pumpEnabled");
        DevicePreferences p = new DevicePreferences();
        p.scope = scope;
        long slots = number(j, "positions"), days = number(j, "horizonDays"),
             duration = number(j, "pumpDurationMs");
        if ((slots != 4 && slots != 5) || days < 1 || days > 7 || duration < 500 || duration > 5000)
            throw new IllegalArgumentException("Configuración fuera de rango");
        p.positions = (int) slots;
        p.horizonDays = (int) days;
        p.pumpDurationMs = (int) duration;
        p.ledEnabled = bool(j, "ledEnabled");
        p.buzzerEnabled = bool(j, "buzzerEnabled");
        p.lcdEnabled = bool(j, "lcdEnabled");
        p.exitSensorEnabled = bool(j, "exitSensorEnabled");
        p.servoEnabled = bool(j, "servoEnabled");
        p.pumpEnabled = bool(j, "pumpEnabled");
        return p;
    }
}
