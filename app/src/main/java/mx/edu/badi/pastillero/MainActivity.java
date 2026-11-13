package mx.edu.badi.pastillero;
import android.Manifest;
import android.app.*;
import android.os.*;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.*;
import com.google.firebase.auth.FirebaseAuth;
import org.json.*;
import java.text.DateFormat;
import java.util.*;

public class MainActivity extends AppCompatActivity {
    // Lectura: El repositorio concentra persistencia y sincronización; la Activity se dedica a presentar y recibir
    // Lectura: eventos.
    private Repository repo;
    // Lectura: Fecha elegida en milisegundos Unix; cero indica que todavía no se seleccionó una dosis.
    private long selectedAt;
    private String connection = "", state = "", draftState = "";
    // Lectura: Relaciona las opciones visibles con IDs estables; borrar una opción no cambia los IDs restantes.
    private final ArrayList<String> ids = new ArrayList<>();
    private final DateFormat dates =
        DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT);
    private TextView status, history, plan, chosen;
    private Spinner compartment, deleteChoice;
    @Override
    // Lectura: Entrada del ciclo de vida: reconstruye controles y observadores; saved permite recuperar la fecha
    // Lectura: elegida.
    public void onCreate(Bundle saved) {
        // Lectura: La clase base prepara el ciclo de vida antes de que esta pantalla registre vistas y observadores.
        super.onCreate(saved);
        // Lectura: Infla activity_main.xml; después findViewById puede encontrar cada control por su identificador.
        setContentView(R.layout.activity_main);
        // Lectura: Ajusta el contenido a las barras del sistema para que no oculten botones; no cambia los datos de
        // Lectura: dosis.
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.root), (v, insets) -> {
            androidx.core.graphics.Insets bars =
                insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });
        status = findViewById(R.id.status);
        history = findViewById(R.id.history);
        plan = findViewById(R.id.plan);
        chosen = findViewById(R.id.chosen);
        compartment = findViewById(R.id.compartment);
        deleteChoice = findViewById(R.id.deleteChoice);
        compartment.setAdapter(
            new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[] {getString(R.string.compartment_1), getString(R.string.compartment_2),
                    getString(R.string.compartment_3)}));
        if (saved != null)
            selectedAt = saved.getLong("selectedAt");
        showChosen();
        repo = new Repository(this);
        repo.connection.observe(this, s -> {
            connection = s;
            showStatus();
        });
        repo.deviceState.observe(this, s -> {
            state = s;
            showStatus();
        });
        // Lectura: LiveData observa el borrador de esta cuenta; this vincula la observación al ciclo de vida de la
        // Lectura: Activity.
        repo.dao.observeDraft(repo.scope).observe(this, this::showPlan);
        repo.dao.observeEvents(repo.scope).observe(this, events -> {
            StringBuilder text = new StringBuilder();
            int confirmed = 0, missed = 0;
            for (DoseEvent e : events) {
                // Lectura: Solo cuenta CONFIRMED físico; los eventos de simulación siguen visibles pero no prueban
                // Lectura: adherencia real.
                if (PlanCodec.confirmed(e))
                    confirmed++;
                if (!e.simulation && "MISSED".equals(e.type))
                    missed++;
                text.append(e.simulation ? "[SIMULACIÓN] " : "")
                    .append(Labels.event(e.type))
                    .append(" · C")
                    .append(e.compartment)
                    .append("\nProgramada: ")
                    .append(dates.format(new Date(e.scheduledAt)))
                    .append("\nRegistrada: ")
                    .append(e.actualAt > 1700000000000L ? dates.format(new Date(e.actualAt))
                                                        : "reloj sin sincronizar");
                if ("CONFIRMED".equals(e.type))
                    text.append(" · diferencia ").append(PlanCodec.delay(e) / 1000).append(" s");
                text.append("\n\n");
            }
            history.setText(getString(R.string.history_summary, confirmed, missed,
                events.isEmpty() ? getString(R.string.no_events) : text.toString()));
        });
        findViewById(R.id.date).setOnClickListener(v -> chooseDate());
        findViewById(R.id.add).setOnClickListener(
            // Lectura: Spinner empieza en índice cero; +1 lo convierte en compartimento 1, 2 o 3.
            v -> repo.add(selectedAt, compartment.getSelectedItemPosition() + 1));
        findViewById(R.id.delete).setOnClickListener(v -> {
            int i = deleteChoice.getSelectedItemPosition();
            if (i >= 0 && i < ids.size())
                repo.remove(ids.get(i));
        });
        // Lectura: El botón comprueba comunicación mediante PING; no ordena mover ni confirma una toma.
        findViewById(R.id.ping).setOnClickListener(v -> repo.ping());
        TextView commands = findViewById(R.id.commands);
        repo.dao.observeCommands(repo.scope).observe(this, items -> {
            StringBuilder lines = new StringBuilder();
            for (CommandRequest item : items)
                lines.append(dates.format(new Date(item.createdAt)))
                    .append(" · ")
                    .append(item.status)
                    .append("\n");
            commands.setText(items.isEmpty()
                    ? getString(R.string.commands_empty, BuildConfig.COMMAND_MODE)
                    : getString(
                          R.string.commands_header, BuildConfig.COMMAND_MODE, lines.toString()));
        });
        findViewById(R.id.sync).setOnClickListener(v -> repo.retry());
        findViewById(R.id.remote)
            .setOnClickListener(v
                -> new AlertDialog.Builder(this)
                    .setTitle(R.string.reload_title)
                    .setMessage(R.string.reload_message)
                    .setPositiveButton(R.string.reload, (d, w) -> repo.reloadRemote())
                    .setNegativeButton(R.string.cancel, null)
                    .show());
        findViewById(R.id.login).setOnClickListener(v -> login());
        findViewById(R.id.logout).setOnClickListener(v -> {
            if (PastilleroApp.cloudReady())
                FirebaseAuth.getInstance().signOut();
            recreate();
        });
        if (Build.VERSION.SDK_INT >= 33)
            requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, 1);
    }
    private void showStatus() {
        status.setText(getString(R.string.status_lines, connection, state, draftState));
    }
    private void showChosen() {
        chosen.setText(selectedAt == 0
                ? getString(R.string.no_date)
                : getString(R.string.chosen_date, dates.format(new Date(selectedAt)),
                      TimeZone.getDefault().getID()));
    }
    // Lectura: Abre selectores de fecha y hora; Calendar convierte la selección local a milisegundos Unix.
    private void chooseDate() {
        Calendar c = Calendar.getInstance();
        new DatePickerDialog(this, (view, y, m, d) -> {
            c.set(y, m, d);
            new TimePickerDialog(this, (time, h, min) -> {
                c.set(Calendar.HOUR_OF_DAY, h);
                c.set(Calendar.MINUTE, min);
                c.set(Calendar.SECOND, 0);
                // Lectura: Elimina fracciones de segundo para que la hora elegida sea precisa al minuto.
                c.set(Calendar.MILLISECOND, 0);
                selectedAt = c.getTimeInMillis();
                showChosen();
            }, c.get(Calendar.HOUR_OF_DAY), c.get(Calendar.MINUTE), true).show();
        }, c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
    }
    // Lectura: Presenta el borrador Room ordenado por fecha y reconstruye las opciones de eliminación.
    private void showPlan(PlanDraft draft) {
        // Lectura: Limpia solo la lista temporal de la pantalla; no borra el historial SQLite.
        ids.clear();
        ArrayList<String> labels = new ArrayList<>();
        StringBuilder text = new StringBuilder();
        if (draft != null) {
            draftState = getString(R.string.draft_status, draft.status, draft.baseRevision);
            try {
                JSONObject json = new JSONObject(draft.json);
                ArrayList<String> sorted = new ArrayList<>();
                json.keys().forEachRemaining(sorted::add);
                sorted.sort(
                    Comparator.comparingLong(id -> json.optJSONObject(id).optLong("scheduledAt")));
                for (String id : sorted) {
                    JSONObject d = json.getJSONObject(id);
                    ids.add(id);
                    String label = "C" + d.getInt("compartment") + " · "
                        + dates.format(new Date(d.getLong("scheduledAt")));
                    labels.add(label);
                    text.append(label).append("\n");
                }
            } catch (Exception e) {
                text.append("No se pudo leer el plan local");
            }
        }
        plan.setText(text.length() == 0 ? getString(R.string.no_schedule) : text.toString());
        deleteChoice.setAdapter(
            new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, labels));
        showStatus();
    }
    // Lectura: Valida campos e inicia Authentication de forma asíncrona; no guarda la contraseña en Room.
    private void login() {
        if (!PastilleroApp.cloudReady()) {
            Toast
                .makeText(this,
                    "Configura Firebase para iniciar sesión. El modo local está disponible.",
                    Toast.LENGTH_LONG)
                .show();
            return;
        }
        String email = ((EditText) findViewById(R.id.email)).getText().toString().trim();
        EditText password = findViewById(R.id.password);
        // Lectura: Lee la contraseña solo para autenticar; no se recorta ni se registra en mensajes o archivos.
        String secret = password.getText().toString();
        if (email.isEmpty() || secret.isEmpty()) {
            Toast.makeText(this, "Introduce correo y contraseña", Toast.LENGTH_SHORT).show();
            return;
        }
        FirebaseAuth.getInstance()
            // Lectura: El SDK autentica en segundo plano y devuelve una Task; la pantalla sigue respondiendo.
            .signInWithEmailAndPassword(email, secret)
            .addOnCompleteListener(t -> {
                // Lectura: Retira la contraseña del campo al terminar la solicitud, tanto en éxito como en fallo.
                password.setText("");
                if (t.isSuccessful())
                    recreate();
                else
                    Toast.makeText(this, "No se pudo iniciar sesión", Toast.LENGTH_LONG).show();
            });
    }
    @Override
    // Lectura: Conserva la fecha al recrear la pantalla; los datos durables ya están en Room.
    protected void onSaveInstanceState(Bundle out) {
        out.putLong("selectedAt", selectedAt);
        super.onSaveInstanceState(out);
    }
    @Override
    // Lectura: Libera listeners y temporizador del repositorio antes de destruir la Activity.
    protected void onDestroy() {
        if (repo != null)
            repo.close();
        super.onDestroy();
    }
}
