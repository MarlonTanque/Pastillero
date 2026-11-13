package mx.edu.badi.pastillero;
import android.app.Application;
import com.google.firebase.*;
import com.google.firebase.database.FirebaseDatabase;

public class PastilleroApp extends Application {
    // Lectura: Valida que la configuración pública esté completa y apunte al proyecto dedicado, antes de activar
    // Lectura: Firebase.
    public static boolean cloudReady() {
        return !BuildConfig.FIREBASE_API_KEY.isEmpty() && !BuildConfig.FIREBASE_APP_ID.isEmpty()
            && BuildConfig.FIREBASE_DATABASE_URL.equals(
                "https://pastillerobadi-default-rtdb.firebaseio.com")
            && BuildConfig.FIREBASE_PROJECT_ID.equals("pastillerobadi");
    }
    @Override
    // Lectura: Application se crea antes que la Activity: prepara Firebase y el canal de avisos una vez por proceso.
    public void onCreate() {
        super.onCreate();
        if (cloudReady()) {
            FirebaseOptions options = new FirebaseOptions.Builder()
                                          .setApiKey(BuildConfig.FIREBASE_API_KEY)
                                          .setApplicationId(BuildConfig.FIREBASE_APP_ID)
                                          .setProjectId(BuildConfig.FIREBASE_PROJECT_ID)
                                          .setDatabaseUrl(BuildConfig.FIREBASE_DATABASE_URL)
                                          .build();
            if (FirebaseApp.getApps(this).isEmpty())
                FirebaseApp.initializeApp(this, options);
            // Lectura: Activa la caché de disco del SDK antes de usar referencias; Room mantiene además su historial y
            // Lectura: cola propios.
            FirebaseDatabase.getInstance().setPersistenceEnabled(true);
        }
        Alerts.createChannel(this);
    }
}
