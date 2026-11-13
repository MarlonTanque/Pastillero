package mx.edu.badi.pastillero;
import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.room.Room;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class RoomOfflineTest {
    @Test
    public void migrationPreservesVersionOneHistoryAndAddsDurableCommands() throws Exception {
        verifyMigration(1);
    }
    @Test
    public void migrationPreservesIntermediateVersionTwoHistory() throws Exception {
        verifyMigration(2);
    }
    private void verifyMigration(int oldVersion) throws Exception {
        Context c = InstrumentationRegistry.getInstrumentation().getTargetContext();
        String name = "migration-" + oldVersion + "-3-test.db";
        c.deleteDatabase(name);
        String schema;
        try (java.io.InputStream in =
                 InstrumentationRegistry.getInstrumentation().getContext().getAssets().open(
                     "mx.edu.badi.pastillero.PastilleroDatabase/" + oldVersion + ".json")) {
            java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int n;
            while ((n = in.read(buffer)) != -1)
                bytes.write(buffer, 0, n);
            schema = bytes.toString("UTF-8");
        }
        org.json.JSONObject old = new org.json.JSONObject(schema).getJSONObject("database");
        android.database.sqlite.SQLiteDatabase legacy =
            android.database.sqlite.SQLiteDatabase.openOrCreateDatabase(
                c.getDatabasePath(name), null);
        org.json.JSONArray entities = old.getJSONArray("entities");
        for (int i = 0; i < entities.length(); i++) {
            org.json.JSONObject entity = entities.getJSONObject(i);
            legacy.execSQL(entity.getString("createSql")
                    .replace("${TABLE_NAME}", entity.getString("tableName")));
        }
        org.json.JSONArray setup = old.getJSONArray("setupQueries");
        for (int i = 0; i < setup.length(); i++)
            legacy.execSQL(setup.getString(i));
        legacy.execSQL("INSERT INTO dose_events VALUES "
                       + "('owner:device','old-event','old-dose','CONFIRMED',1800000000000,"
                       + "1800000001000,2,0)");
        legacy.execSQL(
            "INSERT INTO plan_drafts VALUES ('owner:device','{}','old-token','Pendiente',7,1)");
        legacy.setVersion(oldVersion);
        legacy.close();
        PastilleroDatabase migrated =
            Room.databaseBuilder(c, PastilleroDatabase.class, name)
                .addMigrations(PastilleroDatabase.MIGRATION_1_2, PastilleroDatabase.MIGRATION_2_3, PastilleroDatabase.MIGRATION_3_4)
                .build();
        assertEquals("old-token", migrated.dao().draft("owner:device").token);
        assertEquals(7, migrated.dao().draft("owner:device").baseRevision);
        assertTrue(migrated.dao().draft("owner:device").dirty);
        assertEquals("simulation", migrated.dao().draft("owner:device").targetMode);
        try (android.database.Cursor cursor = migrated.query(
                 "SELECT type,actualAt FROM dose_events WHERE eventId='old-event'", null)) {
            assertTrue(cursor.moveToFirst());
            assertEquals("CONFIRMED", cursor.getString(0));
            assertEquals(1800000001000L, cursor.getLong(1));
        }
        CommandRequest command = new CommandRequest();
        command.scope = "owner:device";
        command.commandId = "stable-id";
        assertTrue(migrated.dao().insertCommand(command) > 0);
        assertEquals(-1, migrated.dao().insertCommand(command));
        migrated.close();
        PastilleroDatabase reopened =
            Room.databaseBuilder(c, PastilleroDatabase.class, name)
                .addMigrations(PastilleroDatabase.MIGRATION_1_2, PastilleroDatabase.MIGRATION_2_3, PastilleroDatabase.MIGRATION_3_4)
                .build();
        assertEquals(1, reopened.dao().pendingCommands(command.scope).size());
        assertEquals(0, reopened.dao().pendingCommands("other:device").size());
        reopened.dao().commandResult(
            command.scope, command.commandId, "COMPLETED", "{\"reason\":\"OK\"}");
        assertTrue(reopened.dao().pendingCommands(command.scope).isEmpty());
        reopened.close();
        c.deleteDatabase(name);
    }
    @Test
    public void draftSurvivesReopenAndScopeIsIsolated() {
        Context c = InstrumentationRegistry.getInstrumentation().getTargetContext();
        String name = "room-offline-test.db";
        c.deleteDatabase(name);
        PastilleroDatabase first = Room.databaseBuilder(c, PastilleroDatabase.class, name).build();
        PlanDraft d = new PlanDraft();
        d.scope = "owner:device";
        d.json = "{}";
        // Lectura: Marca que existe una edición local pendiente de acuse; estar conectado no equivale a estar
        // Lectura: sincronizado.
        d.dirty = true;
        d.token = "a";
        first.dao().saveDraft(d);
        first.close();
        PastilleroDatabase second = Room.databaseBuilder(c, PastilleroDatabase.class, name).build();
        assertTrue(second.dao().draft(d.scope).dirty);
        assertNull(second.dao().draft("other:device"));
        second.dao().acknowledge(d.scope, "wrong", 1);
        assertTrue(second.dao().draft(d.scope).dirty);
        second.dao().acknowledge(d.scope, "a", 1);
        assertFalse(second.dao().draft(d.scope).dirty);
        DoseEvent e = new DoseEvent();
        e.scope = d.scope;
        e.eventId = "event";
        assertTrue(second.dao().insertEvent(e) > 0);
        assertEquals(-1, second.dao().insertEvent(e));
        second.close();
        PastilleroDatabase third = Room.databaseBuilder(c, PastilleroDatabase.class, name).build();
        try (android.database.Cursor cursor = third.query(
                 "SELECT COUNT(*) FROM dose_events WHERE scope=?", new Object[] {d.scope})) {
            assertTrue(cursor.moveToFirst());
            assertEquals(1, cursor.getInt(0));
        }
        third.close();
        c.deleteDatabase(name);
    }
}
