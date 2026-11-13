import { describe, it, expect } from "vitest";
import {
  dayKey,
  monday,
  weekDays,
  moveWeek,
  doseStatus,
  newId,
} from "./calendar";
import type { DoseEvent } from "./types";
describe("fechas y estados del calendario", () => {
  it("la semana empieza el lunes real", () =>
    expect(dayKey(monday(new Date(2026, 9, 20, 12)))).toBe("2026-10-19"));
  it("domingo pertenece al lunes anterior", () =>
    expect(dayKey(monday(new Date(2026, 9, 25)))).toBe("2026-10-19"));
  it("cruza el cambio de año", () =>
    expect(weekDays(new Date(2026, 11, 28)).map(dayKey)).toEqual([
      "2026-12-28",
      "2026-12-29",
      "2026-12-30",
      "2026-12-31",
      "2027-01-01",
      "2027-01-02",
      "2027-01-03",
    ]));
  it("incluye febrero bisiesto", () =>
    expect(weekDays(new Date(2028, 1, 28)).map(dayKey)).toContain(
      "2028-02-29",
    ));
  it("navega a la semana siguiente y vuelve", () =>
    expect(dayKey(moveWeek(moveWeek(new Date(2026, 9, 19), 1), -1))).toBe(
      "2026-10-19",
    ));
  it("una fecha vencida sin evento no se declara omitida", () =>
    expect(doseStatus("a", 1, [], 2)).toBe("SIN_REGISTRO"));
  it("una fecha futura queda programada", () =>
    expect(doseStatus("a", 3, [], 2)).toBe("PROGRAMADA"));
  it("prioriza el último registro de la misma dosis", () => {
    const base = {
      id: "a",
      doseId: "d",
      medicationId: "m",
      scheduledAt: 1,
      compartment: 1,
      simulation: true,
    };
    const es: DoseEvent[] = [
      { ...base, actualAt: 2, type: "STARTED" },
      { ...base, id: "b", actualAt: 3, type: "CONFIRMED" },
    ];
    expect(doseStatus("d", 1, es, 4)).toBe("CONFIRMED");
  });
  it("no mezcla eventos de otra dosis", () =>
    expect(
      doseStatus(
        "d",
        3,
        [
          {
            id: "e",
            doseId: "other",
            medicationId: "m",
            scheduledAt: 1,
            actualAt: 2,
            compartment: 1,
            simulation: false,
            type: "CONFIRMED",
          },
        ],
        2,
      ),
    ).toBe("PROGRAMADA"));
  it("las nuevas pautas reciben identidades UUID distintas", () => {
    const a = newId(),
      b = newId();
    expect(a).toMatch(/^[a-f0-9-]{36}$/);
    expect(a).not.toBe(b);
  });
});
