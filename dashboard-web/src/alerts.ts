import { relative } from "./labels";
import type { Devices } from "./types";

export type Severity = "critical" | "warning" | "info" | "success";
export interface Alert {
  /** Estable por condición (`dispositivo:clave`) o por evento (`dispositivo:event:id`). */
  id: string;
  severity: Severity;
  title: string;
  detail: string;
  deviceId?: string;
  at: number;
  source: "sensor" | "event" | "command" | "system";
}

/** Igual que la app Android: un estado de más de 30 s no se considera conexión reciente. */
export const OFFLINE_MS = 30000;
export const rank: Record<Severity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
  success: 3,
};
export const bySeverity = (a: Alert, b: Alert) =>
  rank[a.severity] - rank[b.severity] || b.at - a.at;

/** Condiciones activas según el último estado V2 de cada dispositivo. */
export function conditions(devices: Devices, now: number): Alert[] {
  const out: Alert[] = [];
  for (const [deviceId, device] of Object.entries(devices)) {
    const s = device.v2?.state;
    if (!s) continue;
    const add = (
      key: string,
      severity: Severity,
      title: string,
      detail: string,
    ) =>
      out.push({
        id: `${deviceId}:${key}`,
        severity,
        title,
        detail,
        deviceId,
        at: now,
        source: "sensor",
      });
    if (!s.updatedAt || now - s.updatedAt > OFFLINE_MS)
      add(
        "offline",
        "critical",
        "Pastillero sin conexión",
        `Última señal ${relative(s.updatedAt, now)}. Las alarmas físicas siguen funcionando en el equipo.`,
      );
    if (s.phase === 7)
      add(
        "failure",
        "critical",
        "Fallo: entregas detenidas",
        "El firmware detuvo las entregas. Revisa el mecanismo antes de reanudar.",
      );
    if (s.phase === 5)
      add(
        "review",
        "critical",
        "Requiere revisión física",
        "Hubo un reinicio o anomalía durante una entrega; reconócela en el equipo.",
      );
    if (s.storageHealthy === false)
      add(
        "storage",
        "critical",
        "Falla de almacenamiento",
        "Sin NVS el pastillero deja de dispensar para no repetir dosis.",
      );
    if (s.blisterPresent === false)
      add(
        "blister",
        "warning",
        "Sin blíster",
        "El sensor no detecta el blíster; las entregas se bloquearán.",
      );
    if (s.calibrated === false)
      add(
        "calibration",
        "warning",
        "Motor sin calibrar",
        "Calibra la posición cero (comandos a/r/c) antes de entregar.",
      );
    if (s.phase === 4)
      add(
        "waiting",
        "info",
        "Esperando confirmación física",
        "El responsable debe pulsar el botón del pastillero.",
      );
    const published = device.v2?.program?.revision;
    if (published && (s.appliedRevision ?? 0) < published)
      add(
        "revision",
        "info",
        "Plan pendiente de aplicar",
        `El equipo tiene la revisión ${s.appliedRevision ?? 0} de ${published}.`,
      );
  }
  return out;
}

const eventAlert: Record<string, [Severity, string, string]> = {
  MISSED: [
    "critical",
    "Dosis omitida",
    "Pasaron cinco minutos sin confirmación física.",
  ],
  BLOCKED: [
    "critical",
    "Entrega bloqueada",
    "No había blíster al momento de la dosis.",
  ],
  RECOVERY: [
    "critical",
    "Reinicio durante una entrega",
    "La dosis no se repite; requiere revisión y calibración.",
  ],
  NO_EXIT: [
    "warning",
    "Sin salida detectada",
    "El sensor no vio salir la pastilla (no confirma omisión).",
  ],
  STARTED: ["info", "Entrega iniciada", "El motor se mueve al compartimento."],
  CONFIRMED: [
    "success",
    "Toma confirmada",
    "El responsable pulsó el botón del pastillero.",
  ],
};

/** Eventos nuevos entre dos lecturas. La primera lectura no alarma por historial antiguo. */
export function newEvents(
  previous: Devices | undefined,
  next: Devices,
): Alert[] {
  if (!previous) return [];
  const out: Alert[] = [];
  for (const [deviceId, device] of Object.entries(next)) {
    const seen = previous[deviceId]?.v2?.events ?? {};
    for (const [key, e] of Object.entries(device.v2?.events ?? {})) {
      if (key in seen) continue;
      const [severity, title, detail] = eventAlert[e.type] ?? [
        "info",
        e.type,
        "Evento del dispositivo.",
      ];
      out.push({
        id: `${deviceId}:event:${key}`,
        severity,
        title: `${title} · C${e.compartment}`,
        detail: e.simulation ? `${detail} (simulación)` : detail,
        deviceId,
        at: e.actualAt || Date.now(),
        source: "event",
      });
    }
  }
  return out.sort(bySeverity);
}
