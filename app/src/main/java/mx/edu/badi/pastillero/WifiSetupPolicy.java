package mx.edu.badi.pastillero;

import java.nio.charset.StandardCharsets;

/** Validación local; nunca devuelve ni registra el contenido de una contraseña. */
public final class WifiSetupPolicy {
    private WifiSetupPolicy() {}
    public static void device(String name, String code) {
        if (name == null || !name.matches("BADI_SETUP_[A-Fa-f0-9]{6}"))
            throw new IllegalArgumentException("El nombre debe ser BADI_SETUP_ seguido de seis caracteres de la etiqueta");
        if (code == null || !code.matches("[A-Fa-f0-9]{24}"))
            throw new IllegalArgumentException("Introduce el código de acceso de 24 caracteres de la etiqueta");
    }
    public static void network(String ssid, String password, boolean open) {
        if (ssid == null || ssid.getBytes(StandardCharsets.UTF_8).length < 1
            || ssid.getBytes(StandardCharsets.UTF_8).length > 32 || controls(ssid))
            throw new IllegalArgumentException("El nombre de red debe ocupar entre 1 y 32 bytes UTF-8");
        if (password == null || controls(password))
            throw new IllegalArgumentException("Contraseña de red no válida");
        int n = password.getBytes(StandardCharsets.UTF_8).length;
        if (open ? n != 0 : !((n >= 8 && n <= 63) || password.matches("[A-Fa-f0-9]{64}")))
            throw new IllegalArgumentException(open ? "Una red abierta debe tener contraseña vacía"
                : "La contraseña debe tener 8 a 63 bytes, o una clave hexadecimal de 64 caracteres");
    }
    private static boolean controls(String text) {
        for (int i = 0; i < text.length(); i++) if (Character.isISOControl(text.charAt(i))) return true;
        return false;
    }
}
