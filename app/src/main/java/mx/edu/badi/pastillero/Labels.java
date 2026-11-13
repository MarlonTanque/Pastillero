package mx.edu.badi.pastillero;
final class Labels {
    static String event(String type) {
        switch (type) {
            case "STARTED":
                return "Entrega iniciada";
            case "CONFIRMED":
                return "Toma confirmada";
            case "MISSED":
                return "Dosis omitida";
            case "BLOCKED":
                return "Entrega bloqueada: revisar blíster";
            case "NO_EXIT":
                return "No se detectó salida: revisar dispositivo";
            case "RECOVERY":
                return "Reinicio durante entrega: revisar dispositivo";
            default:
                return "Evento del dispositivo";
        }
    }
    static String phase(Long phase) {
        if (phase == null)
            return "Sin datos";
        switch (phase.intValue()) {
            case 0:
                return "En espera";
            case 1:
                return "Moviendo al compartimento";
            case 2:
                return "Entregando dosis";
            case 3:
                return "Regresando a cero";
            case 4:
                return "Esperando confirmación física";
            case 5:
                return "Requiere revisión y reconocimiento físico";
            case 6:
                return "Pausa de la secuencia manual";
            case 7:
                return "Fallo: entregas detenidas";
            default:
                return "Estado desconocido";
        }
    }
}
