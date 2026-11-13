package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.room.*;

@Database(entities = {DoseEvent.class, PlanDraft.class, CommandRequest.class, Medication.class,
              DevicePreferences.class, ProgramOutbox.class},
    version = 4,
    // Lectura: Room exporta el esquema de la versión 4 para comprobar migraciones sin cambiar la
    // base del usuario.
    exportSchema = true)
public abstract class PastilleroDatabase extends RoomDatabase {
    public static final androidx.room.migration.Migration MIGRATION_1_2 =
        new androidx.room.migration.Migration(1, 2) {
            @Override
            public void migrate(
                @androidx.annotation.NonNull androidx.sqlite.db.SupportSQLiteDatabase db) {
                db.execSQL("CREATE TABLE IF NOT EXISTS command_requests (scope TEXT NOT NULL, "
                    + "commandId TEXT NOT NULL, json TEXT NOT NULL, status TEXT NOT NULL, "
                    + "resultJson TEXT NOT NULL, createdAt INTEGER NOT NULL, sent INTEGER "
                    + "NOT NULL, PRIMARY KEY(scope,commandId))");
            }
        };
    public static final androidx.room.migration
        .Migration MIGRATION_2_3 = new androidx.room.migration.Migration(2, 3) {
        @Override
        public void migrate(
            @androidx.annotation.NonNull androidx.sqlite.db.SupportSQLiteDatabase db) {
            db.execSQL(
                "ALTER TABLE plan_drafts ADD COLUMN targetMode TEXT NOT NULL DEFAULT 'simulation'");
        }
    };
    /** Solo añade tablas y columna; no hay DROP TABLE ni migración destructiva. */
    public static final androidx.room.migration
        .Migration MIGRATION_3_4 = new androidx.room.migration.Migration(3, 4) {
        @Override
        public void migrate(
            @androidx.annotation.NonNull androidx.sqlite.db.SupportSQLiteDatabase db) {
            db.execSQL("ALTER TABLE command_requests ADD COLUMN protocolVersion INTEGER NOT NULL "
                       + "DEFAULT 1");
            db.execSQL("ALTER TABLE dose_events ADD COLUMN medicationId TEXT NOT NULL DEFAULT ''");
            db.execSQL(
                "CREATE TABLE IF NOT EXISTS medications (scope TEXT NOT NULL, medicationId TEXT "
                + "NOT NULL, name TEXT NOT NULL, mode TEXT NOT NULL, timesJson TEXT NOT NULL, "
                + "zoneId TEXT NOT NULL, compartment INTEGER NOT NULL, intervalMinutes INTEGER NOT "
                + "NULL, startAt INTEGER NOT NULL, endAt INTEGER NOT NULL, enabled INTEGER NOT "
                + "NULL, PRIMARY KEY(scope,medicationId))");
            db.execSQL(
                "CREATE TABLE IF NOT EXISTS device_preferences (scope TEXT NOT NULL, positions "
                + "INTEGER NOT NULL, horizonDays INTEGER NOT NULL, pumpDurationMs INTEGER NOT "
                + "NULL, ledEnabled INTEGER NOT NULL, buzzerEnabled INTEGER NOT NULL, lcdEnabled "
                + "INTEGER NOT NULL, exitSensorEnabled INTEGER NOT NULL, servoEnabled INTEGER NOT "
                + "NULL, pumpEnabled INTEGER NOT NULL, PRIMARY KEY(scope))");
            db.execSQL(
                "CREATE TABLE IF NOT EXISTS program_outbox (scope TEXT NOT NULL, json TEXT NOT "
                + "NULL, token TEXT NOT NULL, status TEXT NOT NULL, baseRevision INTEGER NOT NULL, "
                + "dirty INTEGER NOT NULL, edited INTEGER NOT NULL, PRIMARY KEY(scope))");
        }
    };
    public abstract PastilleroDao dao();
    // Lectura: Instancia compartida visible entre hilos; synchronized evita construir dos bases
    // simultáneamente.
    private static volatile PastilleroDatabase instance;
    // Lectura: Abre pastillero.db con contexto de aplicación y migraciones explícitas; no recrea
    // tablas al actualizar.
    public static PastilleroDatabase get(Context context) {
        if (instance == null)
            synchronized (PastilleroDatabase.class) {
                if (instance == null)
                    instance = Room.databaseBuilder(context.getApplicationContext(),
                                       PastilleroDatabase.class, "pastillero.db")
                                   // Lectura: Conserva filas existentes al pasar de 1 a 2 de 2 a 3
                                   // y de 3 a 4; no se usa Lectura: migración destructiva.
                                   .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4)
                                   .build();
            }
        return instance;
    }
}
