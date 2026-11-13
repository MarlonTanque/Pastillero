package mx.edu.badi.pastillero;
import org.json.*;
import java.util.*;

public final class PlanCodec {
    private PlanCodec() {
    }
    // Lectura: Convierte el borrador JSON a un mapa validado que Realtime Database pueda almacenar.
    public static Map<String, Object> doses(String json) throws JSONException {
        JSONObject root = new JSONObject(json);
        Map<String, Object> result = new TreeMap<>();
        // Compatibilidad V1: máximo 24 fechas. ScheduleEngine valida los programas V2 de 96 dosis.
        if (root.length() > 24)
            throw new IllegalArgumentException("Máximo 24 horarios por plan");
        List<Long> times = new ArrayList<>();
        for (Iterator<String> it = root.keys(); it.hasNext();) {
            String id = it.next();
            if (!id.matches("[A-Za-z0-9-]{1,36}"))
                throw new IllegalArgumentException("ID inválido");
            JSONObject d = root.getJSONObject(id);
            if (d.length() != 2 || !(d.get("scheduledAt") instanceof Number)
                || !(d.get("compartment") instanceof Number))
                throw new IllegalArgumentException("Tipos inválidos");
            long at = d.getLong("scheduledAt");
            int slot = d.getInt("compartment");
            if (d.getDouble("scheduledAt") != at || d.getDouble("compartment") != slot)
                throw new IllegalArgumentException("Los valores deben ser enteros");
            if (slot < 1 || slot > 3 || at < 1700000000000L || at > 4102444800000L)
                throw new IllegalArgumentException("Horario o compartimento inválido");
            for (long time : times)
                // Lectura: Exige al menos diez minutos entre horarios; compara todas las fechas ya recorridas.
                if (Math.abs(time - at) < 600000)
                    throw new IllegalArgumentException("Deja al menos 10 minutos entre dosis");
            times.add(at);
            Map<String, Object> value = new HashMap<>();
            value.put("scheduledAt", at);
            value.put("compartment", slot);
            result.put(id, value);
        }
        return result;
    }
    // Lectura: Calcula hora registrada menos programada en milisegundos; la pantalla divide entre mil para mostrar
    // Lectura: segundos.
    public static long delay(DoseEvent event) {
        return event.actualAt - event.scheduledAt;
    }
    // Lectura: Cuenta como confirmación real únicamente CONFIRMED con simulation=false.
    public static boolean confirmed(DoseEvent event) {
        return "CONFIRMED".equals(event.type) && !event.simulation;
    }
}
