package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.room.Room;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import org.json.*;

public class RoomVersionTwoTest {
    @Test
    public void migrateThreeToFourPreservesHistoryDraftAndCommand() throws Exception {
        Context c = InstrumentationRegistry.getInstrumentation().getTargetContext();
        String name = "qa-v2-migration.db";
        c.deleteDatabase(name);
        String schema;
        try (InputStream in =
                 InstrumentationRegistry.getInstrumentation().getContext().getAssets().open(
                     "mx.edu.badi.pastillero.PastilleroDatabase/3.json")) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] b = new byte[4096];
            int n;
            while ((n = in.read(b)) != -1)
                out.write(b, 0, n);
            schema = out.toString("UTF-8");
        }
        JSONObject old = new JSONObject(schema).getJSONObject("database");
        android.database.sqlite.SQLiteDatabase legacy =
            android.database.sqlite.SQLiteDatabase.openOrCreateDatabase(
                c.getDatabasePath(name), null);
        JSONArray entities = old.getJSONArray("entities");
        for (int i = 0; i < entities.length(); i++) {
            JSONObject e = entities.getJSONObject(i);
            legacy.execSQL(
                e.getString("createSql").replace("${TABLE_NAME}", e.getString("tableName")));
        }
        JSONArray setup = old.getJSONArray("setupQueries");
        for (int i = 0; i < setup.length(); i++)
            legacy.execSQL(setup.getString(i));
        legacy.execSQL(
            "INSERT INTO dose_events VALUES "
            + "('qa:device','event','dose','CONFIRMED',1800000000000,1800000001000,2,0)");
        legacy.execSQL(
            "INSERT INTO plan_drafts (scope,json,token,status,baseRevision,dirty,targetMode) "
            + "VALUES ('qa:device','{}','stable-token','Pendiente',7,1,'simulation')");
        legacy.execSQL("INSERT INTO command_requests VALUES "
                       + "('qa:device','command','{}','Pendiente','',1800000000000,0)");
        legacy.setVersion(3);
        legacy.close();
        PastilleroDatabase db = Room.databaseBuilder(c, PastilleroDatabase.class, name)
                                    .addMigrations(PastilleroDatabase.MIGRATION_3_4)
                                    .build();
        assertEquals("stable-token", db.dao().draft("qa:device").token);
        assertEquals(1, db.dao().pendingCommands("qa:device").size());
        assertEquals(1, db.dao().events("qa:device").size());
        assertEquals("", db.dao().events("qa:device").get(0).medicationId);
        assertTrue(db.dao().medications("qa:device").isEmpty());
        db.close();
        c.deleteDatabase(name);
    }
    @Test
    public void medicationsPreferencesAndOutboxSurviveReopenAndStayScoped() {
        Context c = InstrumentationRegistry.getInstrumentation().getTargetContext();
        String name = "qa-v2-offline.db";
        c.deleteDatabase(name);
        PastilleroDatabase db = Room.databaseBuilder(c, PastilleroDatabase.class, name).build();
        Medication m = new Medication();
        m.scope = "qa:device";
        m.medicationId = "med";
        m.name = "Pauta QA";
        m.startAt = 1800000000000L;
        DevicePreferences p = new DevicePreferences();
        p.scope = m.scope;
        p.positions = 5;
        ProgramOutbox box = new ProgramOutbox();
        box.scope = m.scope;
        box.token = "stable";
        box.dirty = true;
        db.dao().saveMedication(m);
        db.dao().savePreferences(p);
        db.dao().saveProgram(box);
        db.close();
        db = Room.databaseBuilder(c, PastilleroDatabase.class, name).build();
        assertEquals("Pauta QA", db.dao().medications(m.scope).get(0).name);
        assertEquals(5, db.dao().preferences(m.scope).positions);
        assertTrue(db.dao().medications("other:device").isEmpty());
        assertNull(db.dao().program("other:device"));
        db.dao().acknowledgeProgram(m.scope, "wrong", 1);
        assertTrue(db.dao().program(m.scope).dirty);
        db.dao().acknowledgeProgram(m.scope, "stable", 1);
        assertFalse(db.dao().program(m.scope).dirty);
        DoseEvent event = new DoseEvent();
        event.scope = m.scope;
        event.eventId = "historical";
        db.dao().insertEvent(event);
        db.dao().deleteMedication(m.scope, m.medicationId);
        assertEquals(1, db.dao().events(m.scope).size());
        db.close();
        c.deleteDatabase(name);
    }
}
