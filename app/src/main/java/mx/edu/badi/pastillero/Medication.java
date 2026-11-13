package mx.edu.badi.pastillero;

import androidx.annotation.NonNull;
import androidx.room.Entity;

/**
 * Una pauta independiente; las fechas se guardan en UTC y la recurrencia diaria conserva su zona.
 */
@Entity(tableName = "medications", primaryKeys = {"scope", "medicationId"})
public class Medication {
    @NonNull public String scope = "", medicationId = "", name = "";
    @NonNull
    public String mode = "daily",
                  timesJson = "[\"08:00\"]", zoneId = "America/Mexico_City";
    public int compartment = 1, intervalMinutes = 480;
    public long startAt, endAt;
    public boolean enabled = true;
}
