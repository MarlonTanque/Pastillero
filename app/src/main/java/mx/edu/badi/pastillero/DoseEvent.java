package mx.edu.badi.pastillero;

import androidx.annotation.NonNull;
import androidx.room.Entity;

@Entity(tableName = "dose_events", primaryKeys = {"scope", "eventId"})
public class DoseEvent {
    // Lectura: Parte de la clave primaria: cuenta:dispositivo; Room prohíbe NULL y separa los
    // historiales.
    @NonNull public String scope = "";
    // Lectura: Segunda parte de la clave primaria: conserva la clave del evento remoto para ignorar
    // retransmisiones.
    @NonNull public String eventId = "";
    // Lectura: Relaciona el evento con la dosis y distingue STARTED, CONFIRMED, MISSED, BLOCKED y
    // RECOVERY.
    @NonNull @androidx.room.ColumnInfo(defaultValue = "''") public String medicationId = "";
    public String doseId = "", type = "";
    // Lectura: Dos fechas UTC en milisegundos: prevista y realmente registrada; permiten calcular
    // la diferencia.
    public long scheduledAt, actualAt;
    // Lectura: Número de posición de dosis, entre uno y tres; cero se reserva al retorno del
    // mecanismo.
    public int compartment;
    // Lectura: Marca de prueba: un evento simulado no se contabiliza como confirmación física.
    public boolean simulation;
}
