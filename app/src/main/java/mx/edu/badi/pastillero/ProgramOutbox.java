package mx.edu.badi.pastillero;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * Cola V2 separada del borrador V1: la actualización no borra ni publica por accidente el plan
 * anterior.
 */
@Entity(tableName = "program_outbox")
public class ProgramOutbox {
    @PrimaryKey @NonNull public String scope = "";
    @NonNull public String json = "{}", token = "", status = "Sin publicar";
    public long baseRevision;
    public boolean dirty, edited;
}
