import { it, expect } from "vitest";
import { conditions, newEvents, OFFLINE_MS } from "./alerts";
import type { Devices } from "./types";

const now = 1_800_000_000_000;
const device = (state: object, events: object = {}, revision = 3): Devices => ({
  "p-1": {
    v2: {
      program: { revision },
      state: {
        phase: 0,
        calibrated: true,
        storageHealthy: true,
        blisterPresent: true,
        appliedRevision: 3,
        updatedAt: now,
        ...state,
      },
      events: events as never,
    },
  },
});
const ids = (d: Devices) => conditions(d, now).map((a) => [a.id, a.severity]);

it("un pastillero sano no genera alertas", () => {
  expect(conditions(device({}), now)).toEqual([]);
});

it("detecta desconexión, fallos y sensores críticos", () => {
  expect(ids(device({ updatedAt: now - OFFLINE_MS - 1 }))).toEqual([
    ["p-1:offline", "critical"],
  ]);
  expect(ids(device({ phase: 7 }))).toEqual([["p-1:failure", "critical"]]);
  expect(ids(device({ phase: 5 }))).toEqual([["p-1:review", "critical"]]);
  expect(ids(device({ storageHealthy: false }))).toEqual([
    ["p-1:storage", "critical"],
  ]);
  expect(ids(device({ blisterPresent: false, calibrated: false }))).toEqual([
    ["p-1:blister", "warning"],
    ["p-1:calibration", "warning"],
  ]);
  expect(ids(device({ phase: 4, appliedRevision: 2 }))).toEqual([
    ["p-1:waiting", "info"],
    ["p-1:revision", "info"],
  ]);
});

it("solo alarma por eventos nuevos, no por el historial de la primera lectura", () => {
  const ev = (type: string) => ({
    doseId: type,
    type,
    scheduledAt: now,
    actualAt: now,
    compartment: 2,
    simulation: true,
  });
  const first = device({}, { a: ev("CONFIRMED") });
  expect(newEvents(undefined, first)).toEqual([]);
  const next = device(
    {},
    { a: ev("CONFIRMED"), b: ev("MISSED"), c: ev("CONFIRMED") },
  );
  const found = newEvents(first, next);
  expect(found.map((a) => [a.id, a.severity, a.title])).toEqual([
    ["p-1:event:b", "critical", "Dosis omitida · C2"],
    ["p-1:event:c", "success", "Toma confirmada · C2"],
  ]);
});
