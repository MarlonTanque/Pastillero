package mx.edu.badi.pastillero;
import org.junit.Test;
import static org.junit.Assert.*;
import org.json.*;
import java.time.*;
import java.util.*;

public class VersionTwoTest {
    static long at(String s) {
        return Instant.parse(s).toEpochMilli();
    }
    Medication medication() {
        Medication m = new Medication();
        m.medicationId = "medication-a";
        m.name = "Pauta de prueba";
        m.zoneId = "UTC";
        m.startAt = at("2026-01-01T00:00:00Z");
        return m;
    }
    List<ScheduleEngine.Occurrence> expand(Medication m) throws Exception {
        return ScheduleEngine.expand(
            Arrays.asList(m), 4, at("2026-10-19T00:00:00Z"), at("2026-10-26T00:00:00Z"), 96);
    }
    @Test
    public void dailyWeekHasRealSevenDates() throws Exception {
        List<ScheduleEngine.Occurrence> x = expand(medication());
        assertEquals(7, x.size());
        assertEquals(at("2026-10-19T08:00:00Z"), x.get(0).scheduledAt);
        assertEquals(at("2026-10-25T08:00:00Z"), x.get(6).scheduledAt);
    }
    @Test
    public void independentDailyTimesArePreserved() throws Exception {
        Medication m = medication();
        m.timesJson = "[\"08:00\",\"20:00\"]";
        assertEquals(14, expand(m).size());
    }
    @Test
    public void intervalIsAnchoredToItsOwnStart() throws Exception {
        Medication m = medication();
        m.mode = "interval";
        m.startAt = at("2026-10-19T01:15:00Z");
        m.intervalMinutes = 480;
        List<ScheduleEngine.Occurrence> x = expand(m);
        assertEquals(21, x.size());
        assertEquals(at("2026-10-19T09:15:00Z"), x.get(1).scheduledAt);
    }
    @Test
    public void twoMedicinesAtSameTimeRemainIndependent() throws Exception {
        Medication a = medication(), b = medication();
        b.medicationId = "medication-b";
        b.compartment = 2;
        List<ScheduleEngine.Occurrence> x = ScheduleEngine.expand(
            Arrays.asList(a, b), 4, at("2026-10-19T00:00:00Z"), at("2026-10-20T00:00:00Z"), 96);
        assertEquals(2, x.size());
        assertNotEquals(x.get(0).id, x.get(1).id);
    }
    @Test
    public void doseIdsStayStableAcrossRetries() throws Exception {
        assertEquals(expand(medication()).get(0).id, expand(medication()).get(0).id);
    }
    @Test
    public void compartmentChangeGetsNewImmutableDoseIdentity() throws Exception {
        Medication m = medication();
        String old = expand(m).get(0).id;
        m.compartment = 2;
        assertNotEquals(old, expand(m).get(0).id);
    }
    @Test
    public void pauseDoesNotEraseDefinitionOrEmitDose() throws Exception {
        Medication m = medication();
        m.enabled = false;
        assertTrue(expand(m).isEmpty());
        assertEquals("Pauta de prueba", m.name);
    }
    @Test
    public void endBoundaryIsExclusive() throws Exception {
        Medication m = medication();
        m.endAt = at("2026-10-20T08:00:00Z");
        assertEquals(1, expand(m).size());
    }
    @Test
    public void springGapIsSkippedRatherThanShifted() throws Exception {
        Medication m = medication();
        m.zoneId = "America/New_York";
        m.timesJson = "[\"02:30\"]";
        List<ScheduleEngine.Occurrence> x = ScheduleEngine.expand(
            Arrays.asList(m), 4, at("2026-03-07T05:00:00Z"), at("2026-03-10T04:00:00Z"), 96);
        assertEquals(2, x.size());
    }
    @Test
    public void autumnRepeatedHourRunsOnce() throws Exception {
        Medication m = medication();
        m.zoneId = "America/New_York";
        m.timesJson = "[\"01:30\"]";
        List<ScheduleEngine.Occurrence> x = ScheduleEngine.expand(
            Arrays.asList(m), 4, at("2026-11-01T04:00:00Z"), at("2026-11-02T05:00:00Z"), 96);
        assertEquals(1, x.size());
    }
    @Test
    public void fivePositionsAllowFourthDosePosition() throws Exception {
        Medication m = medication();
        m.compartment = 4;
        ScheduleEngine.validate(m, 5);
        assertThrows(IllegalArgumentException.class, () -> ScheduleEngine.validate(m, 4));
    }
    @Test
    public void capacityOverflowFailsWithoutTruncation() {
        Medication m = medication();
        m.mode = "interval";
        m.intervalMinutes = 15;
        assertThrows(IllegalArgumentException.class, () -> expand(m));
    }
    @Test
    public void invalidIntervalsAndDuplicateHoursFail() {
        Medication m = medication();
        m.timesJson = "[\"08:00\",\"08:00\"]";
        assertThrows(IllegalArgumentException.class, () -> expand(m));
        m.mode = "interval";
        m.intervalMinutes = 0;
        assertThrows(IllegalArgumentException.class, () -> expand(m));
    }
    @Test
    public void blankNameAndInvalidZoneFail() {
        Medication m = medication();
        m.name = " ";
        assertThrows(IllegalArgumentException.class, () -> expand(m));
        m.name = "Test";
        m.zoneId = "Made/Up";
        assertThrows(java.time.DateTimeException.class, () -> expand(m));
    }
    @Test
    public void localPreferencesRejectUnsafePumpDuration() throws Exception {
        JSONObject j = ScheduleEngine.preferencesJson(new DevicePreferences());
        j.put("pumpDurationMs", 5001);
        assertThrows(IllegalArgumentException.class, () -> BridgeProtocol.preferences(j, "scope"));
    }
    @Test
    public void messageFromAnotherOriginIsRejected() {
        assertThrows(SecurityException.class,
            () -> BridgeProtocol.parse("{}", "https://attacker.invalid", true));
    }
    @Test
    public void iframeIsRejectedEvenAtTrustedOrigin() {
        assertThrows(SecurityException.class,
            () -> BridgeProtocol.parse("{}", BridgeProtocol.ORIGIN, false));
    }
    @Test
    public void unknownActionAndAdminFieldsAreRejected() throws Exception {
        JSONObject j = new JSONObject()
                           .put("id", "a")
                           .put("version", 1)
                           .put("action", "DISPENSE")
                           .put("payload", new JSONObject());
        assertThrows(IllegalArgumentException.class,
            () -> BridgeProtocol.parse(j.toString(), BridgeProtocol.ORIGIN, true));
        j.put("action", "snapshot").put("admin", true);
        assertThrows(IllegalArgumentException.class,
            () -> BridgeProtocol.parse(j.toString(), BridgeProtocol.ORIGIN, true));
    }
    @Test
    public void validMessageIsParsedAndNotEvaluated() throws Exception {
        JSONObject j = BridgeProtocol.parse(
            "{\"version\":1,\"id\":\"a-1\",\"action\":\"snapshot\",\"payload\":{}}",
            BridgeProtocol.ORIGIN, true);
        assertEquals("snapshot", j.getString("action"));
    }
    @Test
    public void oversizedMessagesAndFractionalNumbersFail() {
        assertThrows(IllegalArgumentException.class,
            ()
                -> BridgeProtocol.parse(
                    String.join("", Collections.nCopies(32769, "x")), BridgeProtocol.ORIGIN, true));
        assertThrows(IllegalArgumentException.class,
            () -> BridgeProtocol.number(new JSONObject().put("n", 1.5), "n"));
    }
    @Test
    public void programContainsModeIndependentDefinitionsAndNoCredentials() throws Exception {
        DevicePreferences p = new DevicePreferences();
        JSONObject j =
            ScheduleEngine.program(Arrays.asList(medication()), p, at("2026-10-19T00:00:00Z"));
        assertEquals(2, j.getInt("version"));
        assertEquals(7, j.getJSONObject("doses").length());
        assertEquals(1, j.getJSONObject("regimens").length());
        assertFalse(j.toString().contains("password"));
        assertFalse(j.toString().contains("idToken"));
    }
    @Test
    public void emptyProgramCanClearFutureSchedules() throws Exception {
        JSONObject j = ScheduleEngine.program(
            Collections.emptyList(), new DevicePreferences(), at("2026-10-19T00:00:00Z"));
        assertEquals(0, j.getJSONObject("doses").length());
    }
}
