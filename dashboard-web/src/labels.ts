import type { Feature } from "./types";

/** Debe coincidir con Features.java (Android) y FEATURES (admin-backend). */
export const FEATURES: { id: Feature; name: string; detail: string }[] = [
  {
    id: "medications",
    name: "Medicamentos",
    detail: "Crear, editar y eliminar pautas y horarios.",
  },
  {
    id: "publish",
    name: "Publicar al pastillero",
    detail:
      "Enviar el plan al ESP32, reintentar y recargar el programa remoto.",
  },
  {
    id: "deviceSettings",
    name: "Ajustes del dispositivo",
    detail: "Posiciones, horizonte, LED, buzzer, bomba, servo, LCD y sensor.",
  },
  {
    id: "diagnostics",
    name: "Diagnóstico y vista clásica",
    detail: "Comprobar conexión (PING) y abrir la vista nativa antigua.",
  },
];

/** Igual que Labels.phase en Android. */
export function phaseName(phase?: number): string {
  switch (phase) {
    case undefined:
      return "Sin datos";
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
      return "Requiere revisión";
    case 6:
      return "Pausa de la secuencia manual";
    case 7:
      return "Fallo: entregas detenidas";
    default:
      return "Estado desconocido";
  }
}

export const eventNames: Record<string, string> = {
  CONFIRMED: "Confirmada",
  MISSED: "Omitida",
  BLOCKED: "Sin blíster",
  RECOVERY: "Revisar reinicio",
  NO_EXIT: "Sin salida detectada",
  STARTED: "Entrega iniciada",
};

export const errorNames: Record<string, string> = {
  INVALID_OR_REVOKED_SESSION:
    "La sesión expiró o fue revocada. Inicia sesión de nuevo.",
  DASHBOARD_ADMIN_REQUIRED:
    "Esta cuenta no es la administradora del dashboard.",
  VERSION_CONFLICT:
    "Otro cambio se aplicó antes. Se recargaron los datos; inténtalo de nuevo.",
  PRIMARY_ADMIN_PROTECTED: "El administrador principal no se puede modificar.",
  ADMIN_ACCOUNT_PROTECTED:
    "Las cuentas administrativas no se pueden modificar desde aquí.",
  ACCOUNT_NOT_PROVISIONED: "La cuenta no tiene registro de acceso en Firebase.",
  FEATURES_ONLY_FOR_OWNER: "Solo las cuentas responsables usan la app.",
  ORIGIN_DENIED:
    "El backend rechazó el origen; revisa `origin` en la configuración privada.",
  SERVICE_UNAVAILABLE: "El backend administrativo no está disponible.",
};

export function relative(ms?: number, now = Date.now()): string {
  if (!ms) return "nunca";
  const s = Math.round((now - ms) / 1000);
  if (s < 10) return "hace segundos";
  if (s < 60) return `hace ${s} s`;
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return new Date(ms).toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
