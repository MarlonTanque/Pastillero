package mx.edu.badi.pastillero;
import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "plan_drafts")
public class PlanDraft {
    @androidx.annotation.NonNull
    @androidx.room.ColumnInfo(defaultValue = "'simulation'")
    // Lectura: Un borrador no cambia de simulación a hardware por actualizar la app; el modo forma parte del contrato.
    public String targetMode = "simulation";
    // Lectura: Una fila de borrador por cuenta:dispositivo; reemplazar ese borrador no reemplaza el historial de
    // Lectura: eventos.
    @PrimaryKey @NonNull public String scope = "";
    // Lectura: json conserva dosis, token identifica la edición y status explica si está pendiente, confirmada o en
    // Lectura: conflicto.
    public String json = "{}", token = "", status = "Sin cambios";
    // Lectura: Revisión remota desde la que se editó; la transacción la compara antes de publicar la siguiente.
    public long baseRevision;
    // Lectura: true significa edición pendiente; solo un acuse del mismo token puede limpiarla.
    public boolean dirty;
}
