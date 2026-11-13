package mx.edu.badi.pastillero;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;

/** Produce datos inertes con el mismo generador de horarios que utiliza el APK. */
public class ContractFixtureTest {
    private JSONObject program(long now, String token) throws Exception {
        List<Medication> medicines = new ArrayList<>();
        for (int compartment = 1; compartment <= 4; compartment++) {
            Medication m = new Medication();
            m.medicationId = "ensayo-" + compartment;
            m.name = "Material inerte " + compartment;
            m.mode = "interval";
            m.zoneId = "UTC";
            m.compartment = compartment;
            m.intervalMinutes = 720;
            m.startAt = now + 180000;
            medicines.add(m);
        }
        DevicePreferences preferences = new DevicePreferences();
        preferences.horizonDays = 1;
        preferences.exitSensorEnabled = true;
        JSONObject result = ScheduleEngine.program(medicines, preferences, now);
        result.put("revision", 1).put("token", token).put("targetMode", "simulation");
        assertEquals(5, result.getInt("positions"));
        assertEquals(8, result.getJSONObject("doses").length());
        assertEquals(4, result.getJSONObject("regimens").length());
        return result;
    }

    @Test
    public void exportNativeProgramsForLocalContractIntegration() throws Exception {
        long now = System.currentTimeMillis();
        JSONObject fixtures = new JSONObject()
            .put("generatedAt", now)
            .put("future", program(now, "ensayo-futuro"))
            // Simula un programa aceptado antes de una desconexión, no una escritura nueva válida.
            .put("cached", program(now - 900000, "ensayo-cache"));
        Path root = Paths.get("..").toAbsolutePath().normalize();
        assertTrue("La prueba debe ejecutarse desde el módulo app", Files.isDirectory(root.resolve("reports")));
        Files.write(root.resolve("reports/integration-v2-programs.json"),
            fixtures.toString(2).getBytes(StandardCharsets.UTF_8));
    }
}
