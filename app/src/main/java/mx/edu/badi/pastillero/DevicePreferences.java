package mx.edu.badi.pastillero;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

/** Preferencias de la pauta. Habilitar un periférico no elimina su bloqueo local del firmware. */
@Entity(tableName = "device_preferences")
public class DevicePreferences {
    @PrimaryKey @NonNull public String scope = "";
    public int positions = 5, horizonDays = 7, pumpDurationMs = 2000;
    public boolean ledEnabled = true, buzzerEnabled = true;
    public boolean lcdEnabled, exitSensorEnabled, servoEnabled, pumpEnabled;
}
