package com.espressif.provisioning;
/** Desactiva TODOS los registros del SDK: upstream registraba PoP y contraseñas incluso en debug. */
public final class PrivateLog {
    private PrivateLog() {}
    public static int d(String tag, Object... values) { return 0; }
    public static int e(String tag, Object... values) { return 0; }
    public static int i(String tag, Object... values) { return 0; }
    public static int w(String tag, Object... values) { return 0; }
    public static int v(String tag, Object... values) { return 0; }
}
