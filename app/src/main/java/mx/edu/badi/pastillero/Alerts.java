package mx.edu.badi.pastillero;
import android.Manifest;
import android.app.*;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

public final class Alerts {
    // Lectura: En Android 8 o superior registra el canal de avisos; versiones anteriores no
    // necesitan canales.
    static void createChannel(Context c) {
        if (Build.VERSION.SDK_INT >= 26)
            c.getSystemService(NotificationManager.class)
                .createNotificationChannel(new NotificationChannel(
                    "doses", "Alertas de dosis", NotificationManager.IMPORTANCE_HIGH));
    }
    // Lectura: Solo avisa por omisión, bloqueo o recuperación; depende de que la app reciba el
    // evento, sin FCM Lectura: garantizado.
    static void event(Context c, DoseEvent e) {
        if (!e.type.equals("MISSED") && !e.type.equals("BLOCKED") && !e.type.equals("RECOVERY")
            && !e.type.equals("NO_EXIT"))
            return;
        // Lectura: Desde Android 13 se comprueba el permiso de notificaciones; sin permiso conserva
        // el evento pero no Lectura: muestra aviso.
        if (Build.VERSION.SDK_INT >= 33
            && ContextCompat.checkSelfPermission(c, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED)
            return;
        c.getSystemService(NotificationManager.class)
            .notify((e.scope + e.eventId).hashCode(),
                new NotificationCompat.Builder(c, "doses")
                    .setSmallIcon(android.R.drawable.ic_dialog_alert)
                    .setContentTitle(e.simulation ? "Prueba del pastillero" : "Revisar pastillero")
                    .setContentText(Labels.event(e.type) + " · compartimento " + e.compartment)
                    .setAutoCancel(true)
                    .build());
    }
}
