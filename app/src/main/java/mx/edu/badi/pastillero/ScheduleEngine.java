package mx.edu.badi.pastillero;

import java.nio.charset.StandardCharsets;
import java.time.*;
import java.util.*;
import org.json.*;

/** Expansión determinista: la misma pauta y fecha producen siempre el mismo ID de dosis. */
public final class ScheduleEngine {
    public static final int MAX_DEVICE_DOSES = 96;
    private ScheduleEngine() {
    }
    public static final class Occurrence {
        public final String id, medicationId, name;
        public final long scheduledAt;
        public final int compartment;
        Occurrence(Medication m, long at) {
            id = UUID.nameUUIDFromBytes(
                         ("badi-v2:" + m.medicationId + ":" + at + ":" + m.compartment)
                             .getBytes(StandardCharsets.UTF_8))
                     .toString();
            medicationId = m.medicationId;
            name = m.name;
            scheduledAt = at;
            compartment = m.compartment;
        }
        public JSONObject json() throws JSONException {
            return new JSONObject()
                .put("id", id)
                .put("medicationId", medicationId)
                .put("name", name)
                .put("scheduledAt", scheduledAt)
                .put("compartment", compartment);
        }
    }
    public static void validate(Medication m, int positions) throws JSONException {
        if (positions != 4 && positions != 5)
            throw new IllegalArgumentException("Elige 4 o 5 posiciones");
        if (!m.medicationId.matches("[A-Za-z0-9-]{1,36}") || m.name.trim().isEmpty()
            || m.name.length() > 80)
            throw new IllegalArgumentException("Identificador o nombre inválido");
        if (m.compartment < 1 || m.compartment >= positions)
            throw new IllegalArgumentException(
                "Cero está reservado al retorno; revisa el compartimento");
        if (m.startAt < 1700000000000L || m.startAt > 4102444800000L
            || (m.endAt != 0 && (m.endAt <= m.startAt || m.endAt > 4102444800000L)))
            throw new IllegalArgumentException("Fechas de pauta inválidas");
        ZoneId.of(m.zoneId);
        if ("daily".equals(m.mode)) {
            JSONArray times = new JSONArray(m.timesJson);
            if (times.length() < 1 || times.length() > 6)
                throw new IllegalArgumentException("Usa de 1 a 6 horas diarias");
            Set<String> unique = new HashSet<>();
            for (int i = 0; i < times.length(); i++) {
                String time = times.getString(i);
                if (!time.matches("(?:[01][0-9]|2[0-3]):[0-5][0-9]") || !unique.add(time))
                    throw new IllegalArgumentException("Horas inválidas o repetidas");
                LocalTime.parse(time);
            }
        } else if (!"interval".equals(m.mode) || m.intervalMinutes < 15
            || m.intervalMinutes > 10080)
            throw new IllegalArgumentException("Intervalo: de 15 minutos a 7 días");
    }
    public static List<Occurrence> expand(List<Medication> medications, int positions, long from,
        long until, int limit) throws JSONException {
        if (until <= from || until - from > 32L * 86400000L || limit < 1 || limit > 4096)
            throw new IllegalArgumentException("Ventana de calendario inválida");
        List<Occurrence> out = new ArrayList<>();
        for (Medication m : medications) {
            validate(m, positions);
            if (!m.enabled)
                continue;
            long begin = Math.max(from, m.startAt),
                 end = m.endAt == 0 ? until : Math.min(until, m.endAt);
            if (end <= begin)
                continue;
            if ("interval".equals(m.mode)) {
                long interval = m.intervalMinutes * 60000L;
                long n = Math.max(0, (begin - m.startAt + interval - 1) / interval);
                for (long at = m.startAt + n * interval; at < end; at += interval)
                    add(out, m, at, limit);
            } else {
                ZoneId zone = ZoneId.of(m.zoneId);
                LocalDate day = Instant.ofEpochMilli(begin).atZone(zone).toLocalDate();
                LocalDate last = Instant.ofEpochMilli(end - 1).atZone(zone).toLocalDate();
                JSONArray times = new JSONArray(m.timesJson);
                while (!day.isAfter(last)) {
                    for (int i = 0; i < times.length(); i++) {
                        LocalDateTime local =
                            LocalDateTime.of(day, LocalTime.parse(times.getString(i)));
                        // Una hora inexistente por cambio estacional se omite; una hora ambigua se
                        // ejecuta una vez.
                        if (zone.getRules().getValidOffsets(local).isEmpty())
                            continue;
                        long at = local.atZone(zone).toInstant().toEpochMilli();
                        if (at >= begin && at < end)
                            add(out, m, at, limit);
                    }
                    day = day.plusDays(1);
                }
            }
        }
        out.sort(
            Comparator.comparingLong((Occurrence x) -> x.scheduledAt).thenComparing(x -> x.id));
        return out;
    }
    private static void add(List<Occurrence> out, Medication m, long at, int limit) {
        if (out.size() >= limit)
            throw new IllegalArgumentException(
                "La ventana supera " + limit + " dosis; reduce días o frecuencias");
        out.add(new Occurrence(m, at));
    }
    public static JSONObject medicationJson(Medication m) throws JSONException {
        return new JSONObject()
            .put("id", m.medicationId)
            .put("name", m.name)
            .put("mode", m.mode)
            .put("times", new JSONArray(m.timesJson))
            .put("zoneId", m.zoneId)
            .put("compartment", m.compartment)
            .put("intervalMinutes", m.intervalMinutes)
            .put("startAt", m.startAt)
            .put("endAt", m.endAt)
            .put("enabled", m.enabled);
    }
    public static JSONObject preferencesJson(DevicePreferences p) throws JSONException {
        return new JSONObject()
            .put("positions", p.positions)
            .put("horizonDays", p.horizonDays)
            .put("ledEnabled", p.ledEnabled)
            .put("buzzerEnabled", p.buzzerEnabled)
            .put("lcdEnabled", p.lcdEnabled)
            .put("exitSensorEnabled", p.exitSensorEnabled)
            .put("servoEnabled", p.servoEnabled)
            .put("pumpEnabled", p.pumpEnabled)
            .put("pumpDurationMs", p.pumpDurationMs);
    }
    public static JSONObject program(List<Medication> meds, DevicePreferences p, long now)
        throws JSONException {
        if (p.horizonDays < 1 || p.horizonDays > 7 || p.pumpDurationMs < 500
            || p.pumpDurationMs > 5000)
            throw new IllegalArgumentException("Preferencias fuera de rango");
        // Ventana explícita: nunca se trunca una pauta sin informar al responsable.
        long from = now + 120000, until = from + p.horizonDays * 86400000L;
        JSONObject doses = new JSONObject(), regimens = new JSONObject();
        for (Medication m : meds)
            regimens.put(m.medicationId, medicationJson(m));
        for (Occurrence d : expand(meds, p.positions, from, until, MAX_DEVICE_DOSES))
            doses.put(d.id,
                new JSONObject()
                    .put("scheduledAt", d.scheduledAt)
                    .put("compartment", d.compartment)
                    .put("medicationId", d.medicationId));
        return new JSONObject()
            .put("version", 2)
            .put("positions", p.positions)
            .put("settings", preferencesJson(p))
            .put("windowStart", from)
            .put("windowEnd", until)
            .put("regimens", regimens)
            .put("doses", doses);
    }
}
