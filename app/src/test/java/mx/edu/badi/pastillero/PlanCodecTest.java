package mx.edu.badi.pastillero;
import org.junit.Test;
import static org.junit.Assert.*;

public class PlanCodecTest {
    private String dose(long at, int slot) {
        return "{\"scheduledAt\":" + at + ",\"compartment\":" + slot + "}";
    }
    @Test
    public void acceptsEmptyPlan() throws Exception {
        assertTrue(PlanCodec.doses("{}").isEmpty());
    }
    @Test
    public void acceptsThreeCompartments() throws Exception {
        for (int i = 1; i <= 3; i++)
            assertEquals(1, PlanCodec.doses("{\"id\":" + dose(1800000000000L, i) + "}").size());
    }
    @Test(expected = IllegalArgumentException.class)
    public void rejectsBlindSlot() throws Exception {
        PlanCodec.doses("{\"id\":" + dose(1800000000000L, 0) + "}");
    }
    @Test(expected = IllegalArgumentException.class)
    public void rejectsOverlappingDoses() throws Exception {
        PlanCodec.doses(
            "{\"a\":" + dose(1800000000000L, 1) + ",\"b\":" + dose(1800000599999L, 2) + "}");
    }
    @Test
    public void acceptsTenMinuteBoundary() throws Exception {
        assertEquals(2,
            PlanCodec
                .doses(
                    "{\"a\":" + dose(1800000000000L, 1) + ",\"b\":" + dose(1800000600000L, 2) + "}")
                .size());
    }
    @Test(expected = IllegalArgumentException.class)
    public void rejectsInvalidId() throws Exception {
        PlanCodec.doses("{\"bad/id\":" + dose(1800000000000L, 1) + "}");
    }
    @Test(expected = IllegalArgumentException.class)
    public void rejectsTwentyFiveDoses() throws Exception {
        StringBuilder j = new StringBuilder("{");
        for (int i = 0; i < 25; i++) {
            if (i > 0)
                j.append(',');
            j.append('"').append(i).append("\":").append(dose(1800000000000L + i * 600000L, 1));
        }
        PlanCodec.doses(j.append('}').toString());
    }
    @Test
    public void simulationCannotCountAsMedicalAdherence() {
        DoseEvent e = new DoseEvent();
        e.type = "CONFIRMED";
        e.simulation = true;
        assertFalse(PlanCodec.confirmed(e));
        e.simulation = false;
        assertTrue(PlanCodec.confirmed(e));
    }
    @Test
    public void comparesActualAndScheduledTime() {
        DoseEvent e = new DoseEvent();
        e.scheduledAt = 1800000000000L;
        e.actualAt = e.scheduledAt + 90000;
        assertEquals(90000, PlanCodec.delay(e));
    }
}
