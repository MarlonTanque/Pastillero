package com.espressif.provisioning;
import org.json.*;
/** Política adicional: la negociación nunca puede desactivar cifrado ni prueba de posesión. */
public final class SecureCapabilities {
    private SecureCapabilities() {}
    public static void requireSecurity1(String json, String pop) throws JSONException {
        JSONObject p = new JSONObject(json).getJSONObject("prov");
        if (p.optInt("sec_ver", -1) != 1 || pop == null || !pop.matches("[A-Fa-f0-9]{24}"))
            throw new SecurityException("Security1 y código del dispositivo requeridos");
        JSONArray caps = p.optJSONArray("cap");
        if (caps != null) for (int i=0; i<caps.length(); i++)
            if ("no_pop".equals(caps.optString(i))) throw new SecurityException("PoP obligatorio");
    }
}
