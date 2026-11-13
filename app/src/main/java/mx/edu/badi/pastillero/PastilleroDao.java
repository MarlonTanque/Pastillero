package mx.edu.badi.pastillero;
import androidx.lifecycle.LiveData;
import androidx.room.*;
import java.util.List;

@Dao
public interface PastilleroDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE) long insertCommand(CommandRequest command);
    // Lectura: Consulta pendientes de esta cuenta en orden de creación; :scope es parámetro
    // enlazado, no texto Lectura: concatenado.
    @Query("SELECT * FROM command_requests WHERE scope=:scope AND sent=0 ORDER BY createdAt")
    List<CommandRequest> pendingCommands(String scope);
    // Lectura: Observa las cincuenta solicitudes más recientes de este ámbito; LIMIT limita la
    // vista y no elimina Lectura: filas.
    @Query("SELECT * FROM command_requests WHERE scope=:scope ORDER BY createdAt DESC LIMIT 50")
    LiveData<List<CommandRequest>> observeCommands(String scope);
    @Query("UPDATE command_requests SET status=:status,sent=:sent WHERE scope=:scope AND "
        + "commandId=:id AND resultJson='' ")
    void
    commandStatus(String scope, String id, String status, boolean sent);
    @Query("UPDATE command_requests SET status=:status,resultJson=:json,sent=1 WHERE scope=:scope "
        + "AND commandId=:id")
    void
    commandResult(String scope, String id, String status, String json);
    // Lectura: Room devuelve el ID insertado o -1 si ya existía; el historial repetido no vuelve a
    // disparar la misma Lectura: alerta.
    @Insert(onConflict = OnConflictStrategy.IGNORE) long insertEvent(DoseEvent event);
    @Query("SELECT * FROM dose_events WHERE scope=:scope ORDER BY actualAt DESC, eventId DESC "
        + "LIMIT 500")
    LiveData<List<DoseEvent>>
    observeEvents(String scope);
    // Lectura: Sustituye únicamente el borrador de ese scope; no borra las tablas de eventos ni de
    // comandos.
    @Insert(onConflict = OnConflictStrategy.REPLACE) void saveDraft(PlanDraft draft);
    // Lectura: Lee una instantánea del borrador en el hilo de trabajo; la variante LiveData
    // notifica cambios a la Lectura: pantalla.
    @Query("SELECT * FROM plan_drafts WHERE scope=:scope") PlanDraft draft(String scope);
    @Query("SELECT * FROM plan_drafts WHERE scope=:scope")
    LiveData<PlanDraft> observeDraft(String scope);
    @Query("UPDATE plan_drafts SET dirty=0, baseRevision=:revision, status='Sincronizado con "
        + "Firebase' WHERE scope=:scope AND token=:token")
    void
    acknowledge(String scope, String token, long revision);
    @Query("UPDATE plan_drafts SET status=:status WHERE scope=:scope AND token=:token")
    void status(String scope, String token, String status);

    // Tablas V2 independientes: no sustituyen el historial ni el borrador de la vista clásica.
    @Insert(onConflict = OnConflictStrategy.REPLACE) void saveMedication(Medication medication);
    @Query("SELECT * FROM medications WHERE scope=:scope ORDER BY name,medicationId")
    List<Medication> medications(String scope);
    @Query("SELECT * FROM medications WHERE scope=:scope ORDER BY name,medicationId")
    LiveData<List<Medication>> observeMedications(String scope);
    @Query("DELETE FROM medications WHERE scope=:scope AND medicationId=:id")
    void deleteMedication(String scope, String id);
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void savePreferences(DevicePreferences preferences);
    @Query("SELECT * FROM device_preferences WHERE scope=:scope")
    DevicePreferences preferences(String scope);
    @Insert(onConflict = OnConflictStrategy.REPLACE) void saveProgram(ProgramOutbox outbox);
    @Query("SELECT * FROM program_outbox WHERE scope=:scope") ProgramOutbox program(String scope);
    @Query("SELECT * FROM program_outbox WHERE scope=:scope")
    LiveData<ProgramOutbox> observeProgram(String scope);
    @Query("UPDATE program_outbox SET dirty=0,baseRevision=:revision,status='Publicado; esperando "
           + "revisión aplicada' WHERE scope=:scope AND token=:token")
    void
    acknowledgeProgram(String scope, String token, long revision);
    @Query("UPDATE program_outbox SET status=:status WHERE scope=:scope AND token=:token")
    void programStatus(String scope, String token, String status);
    @Query("SELECT * FROM dose_events WHERE scope=:scope ORDER BY actualAt DESC,eventId DESC LIMIT "
           + "500")
    List<DoseEvent>
    events(String scope);
    @Query("SELECT * FROM command_requests WHERE scope=:scope AND protocolVersion=2 ORDER BY "
           + "createdAt DESC LIMIT 1")
    CommandRequest
    latestV2Command(String scope);
}
