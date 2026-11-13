import type { DoseEvent } from "./types";
export function dayKey(value: number | Date): string {
  const d = new Date(value);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
export function monday(value: number | Date = new Date()): Date {
  const d = new Date(value);
  return new Date(
    d.getFullYear(),
    d.getMonth(),
    d.getDate() - ((d.getDay() + 6) % 7),
  );
}
export function moveWeek(start: Date, delta: number): Date {
  return new Date(
    start.getFullYear(),
    start.getMonth(),
    start.getDate() + 7 * delta,
  );
}
export function weekDays(start: Date): Date[] {
  return Array.from(
    { length: 7 },
    (_, i) =>
      new Date(start.getFullYear(), start.getMonth(), start.getDate() + i),
  );
}
export const clock = (at: number) =>
  new Intl.DateTimeFormat("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(at);
export const fullDate = (at: number) =>
  new Intl.DateTimeFormat("es-MX", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(at);
export function doseStatus(
  id: string,
  at: number,
  events: DoseEvent[],
  now: number,
): string {
  const event = events
    .filter((x) => x.doseId === id)
    .sort((a, b) => b.actualAt - a.actualAt)[0];
  if (event) return event.type;
  return at < now ? "SIN_REGISTRO" : "PROGRAMADA";
}
export function localInput(at: number): string {
  const d = new Date(at);
  return `${dayKey(d)}T${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
export function newId(): string {
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 15) | 64;
  b[8] = (b[8] & 63) | 128;
  const s = Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
  return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${s.slice(16, 20)}-${s.slice(20)}`;
}
