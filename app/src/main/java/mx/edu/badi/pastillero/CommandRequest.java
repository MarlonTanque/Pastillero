package mx.edu.badi.pastillero;
import androidx.annotation.NonNull;
import androidx.room.Entity;

@Entity(tableName = "command_requests", primaryKeys = {"scope", "commandId"})
public class CommandRequest {
    @NonNull
    // Lectura: La solicitud pertenece a cuenta:dispositivo; commandId completa la clave primaria
    // para impedir Lectura: duplicados.
    public String scope = "",
                  // Lectura: ID estable, solicitud serializada, estado visible y respuesta
                  // separada; vacío significa Lectura: que aún no hay resultado.
        commandId = "", json = "{}", status = "Pendiente", resultJson = "";
    // Lectura: Fecha original de creación de la solicitud en milisegundos UTC.
    @androidx.room.ColumnInfo(defaultValue = "1") public int protocolVersion = 1;
    public long createdAt;
    // Lectura: Indica que ya se envió o cerró localmente; no afirma que exista una respuesta del
    // dispositivo.
    public boolean sent;
}
