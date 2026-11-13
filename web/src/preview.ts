import { defaults, type Action, type Medication, type Snapshot } from "./types";
import { monday, weekDays, dayKey } from "./calendar";
/** Vista del navegador para estudiar/diseñar. Nunca autentica ni contacta Firebase o hardware. */
export function preview(
  action: Action,
  payload: Record<string, unknown>,
): Snapshot {
  let data: Snapshot;
  try {
    data = JSON.parse(
      localStorage.getItem("badi-preview") || "null",
    ) as Snapshot;
  } catch {
    data = null as unknown as Snapshot;
  }
  if (!data)
    data = {
      medications: [],
      occurrences: [],
      events: [],
      settings: { ...defaults },
      device: {},
      signedIn: false,
      authorized: false,
      simulation: true,
      connection: "Vista web local · sin Firebase ni dispositivo",
      programStatus: "Demostración en el navegador",
      revision: 0,
      pending: false,
      now: Date.now(),
      weekStart: +monday(),
      preview: true,
    };
  if (
    action === "signIn" ||
    action === "signOut" ||
    action === "nativeView" ||
    action === "ping" ||
    action === "reload" ||
    action === "rebase"
  )
    throw new Error("Esta acción está disponible dentro del APK Android.");
  if (action === "saveMedication") {
    const m = payload as unknown as Medication;
    if (!m.name.trim()) throw new Error("Escribe el nombre.");
    data.medications = [...data.medications.filter((x) => x.id !== m.id), m];
    data.pending = true;
  }
  if (action === "deleteMedication") {
    data.medications = data.medications.filter((x) => x.id !== payload.id);
    data.pending = true;
  }
  if (action === "savePreferences") {
    data.settings = payload as unknown as Snapshot["settings"];
    data.pending = true;
  }
  if (action === "publish") {
    data.programStatus = "Vista web: no se publica en Firebase";
    data.pending = false;
  }
  data.weekStart =
    typeof payload.weekStart === "number" ? payload.weekStart : data.weekStart;
  data.now = Date.now();
  data.occurrences = [];
  const days = weekDays(new Date(data.weekStart)),
    end = +new Date(
      days[6].getFullYear(),
      days[6].getMonth(),
      days[6].getDate() + 1,
    );
  for (const m of data.medications) {
    if (!m.enabled) continue;
    if (m.mode === "interval") {
      const step = m.intervalMinutes * 60000;
      if (step < 900000) continue;
      for (
        let at =
          m.startAt +
          Math.max(0, Math.ceil((data.weekStart - m.startAt) / step)) * step;
        at < end;
        at += step
      ) {
        if ((!m.endAt || at < m.endAt) && data.occurrences.length < 4096)
          data.occurrences.push({
            id: `${m.id}:${at}`,
            name: m.name,
            medicationId: m.id,
            scheduledAt: at,
            compartment: m.compartment,
          });
      }
    } else
      for (const d of days)
        for (const time of m.times) {
          const at = +new Date(`${dayKey(d)}T${time}`);
          if (at >= m.startAt && (!m.endAt || at < m.endAt))
            data.occurrences.push({
              id: `${m.id}:${at}`,
              name: m.name,
              medicationId: m.id,
              scheduledAt: at,
              compartment: m.compartment,
            });
        }
  }
  data.occurrences.sort((a, b) => a.scheduledAt - b.scheduledAt);
  localStorage.setItem("badi-preview", JSON.stringify(data));
  return data;
}
