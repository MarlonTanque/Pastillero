import { ApiError, type AdminApi, type SimKind } from "./api";
import type { AccessRecord, AdminUser, Devices } from "./types";

/**
 * Demostración en memoria para diseñar sin Firebase. Datos ficticios; no es un cliente de producción
 * y reproduce solo las validaciones visibles (versión, cuentas protegidas, solo responsables).
 */
export function demoApi(now = Date.now()): AdminApi {
  let signedIn = false;
  const listeners = new Set<(v: boolean) => void>();
  const users: AdminUser[] = [
    {
      uid: "admin-demo",
      email: "admin@demo.test",
      disabled: false,
      protected: true,
      access: null,
    },
    {
      uid: "responsable-demo",
      email: "responsable@demo.test",
      disabled: false,
      protected: false,
      access: {
        role: "owner",
        enabled: true,
        version: 3,
        revokedAt: 0,
        features: { diagnostics: false },
      },
    },
    {
      uid: "esp32-demo",
      email: "esp32@demo.test",
      disabled: false,
      protected: false,
      access: { role: "device", enabled: true, version: 1, revokedAt: 0 },
    },
    {
      uid: "responsable-2-demo",
      email: "familiar@demo.test",
      disabled: true,
      protected: false,
      access: {
        role: "owner",
        enabled: false,
        version: 2,
        revokedAt: Math.floor(now / 1000) - 86400,
      },
    },
  ];
  const at = (h: number, m: number, days = 0) => {
    const d = new Date(now);
    d.setDate(d.getDate() + days);
    d.setHours(h, m, 0, 0);
    return +d;
  };
  const devices: Devices = {
    "pastillero-01": {
      ownerUid: "responsable-demo",
      deviceUid: "esp32-demo",
      v2: {
        program: {
          revision: 7,
          positions: 5,
          targetMode: "simulation",
          regimens: {
            a: {
              id: "a",
              name: "Material de ensayo A",
              mode: "daily",
              times: ["08:00", "20:00"],
              compartment: 1,
              enabled: true,
            },
            b: {
              id: "b",
              name: "Material de ensayo B",
              mode: "interval",
              intervalMinutes: 480,
              compartment: 2,
              enabled: true,
            },
            c: {
              id: "c",
              name: "Material de ensayo C",
              mode: "daily",
              times: ["14:00"],
              compartment: 4,
              enabled: false,
            },
          },
        },
        state: {
          phase: 0,
          calibrated: true,
          appliedRevision: 7,
          updatedAt: now - 12000,
          simulation: true,
          storageHealthy: true,
          blisterPresent: true,
          exitDetected: false,
          pumpActive: false,
          servoOpen: false,
          positions: 5,
        },
        events: {
          e1: {
            doseId: "d1",
            type: "CONFIRMED",
            scheduledAt: at(8, 0),
            actualAt: at(8, 2),
            compartment: 1,
            simulation: true,
          },
          e2: {
            doseId: "d2",
            type: "MISSED",
            scheduledAt: at(20, 0, -1),
            actualAt: at(20, 5, -1),
            compartment: 1,
            simulation: true,
          },
          e3: {
            doseId: "d3",
            type: "CONFIRMED",
            scheduledAt: at(6, 0),
            actualAt: at(6, 1),
            compartment: 2,
            simulation: true,
          },
        },
      },
    },
  };
  const find = (uid: string) => {
    const user = users.find((u) => u.uid === uid);
    if (!user) throw new ApiError(404, "ACCOUNT_NOT_PROVISIONED");
    if (user.protected) throw new ApiError(409, "PRIMARY_ADMIN_PROTECTED");
    if (!user.access) throw new ApiError(404, "ACCOUNT_NOT_PROVISIONED");
    return user as AdminUser & { access: AccessRecord };
  };
  const bump = (
    user: AdminUser & { access: AccessRecord },
    expected: number,
    patch: Partial<AccessRecord>,
  ) => {
    if (user.access.version !== expected)
      throw new ApiError(409, "VERSION_CONFLICT");
    user.access = {
      ...user.access,
      ...patch,
      version: expected + 1,
      updatedAt: Date.now(),
      updatedBy: "admin-demo",
    };
    return structuredClone(user.access);
  };
  const ok = <T>(value: T) => Promise.resolve(structuredClone(value));
  // Simulación en vivo: latido cada lectura y escenarios que cambian sensores y eventos.
  const device = devices["pastillero-01"].v2!;
  const state = device.state!;
  let offline = false,
    seq = 0;
  const timers: ReturnType<typeof setTimeout>[] = [];
  const later = (ms: number, fn: () => void) => timers.push(setTimeout(fn, ms));
  const event = (type: string, compartment: number) => {
    const t = Date.now();
    device.events![`sim-${++seq}`] = {
      doseId: `sim-dose-${seq}`,
      type,
      scheduledAt: t,
      actualAt: t,
      compartment,
      simulation: true,
    };
  };
  const simulate = (kind: SimKind) => {
    switch (kind) {
      case "deliver":
        // Ciclo real del firmware: mover → entregar → regresar a cero → esperar botón → confirmar.
        Object.assign(state, { phase: 1 });
        later(1500, () => {
          event("STARTED", 1);
          Object.assign(state, {
            phase: 2,
            servoOpen: true,
            exitDetected: true,
          });
        });
        later(3500, () => Object.assign(state, { phase: 3, servoOpen: false }));
        later(5000, () => Object.assign(state, { phase: 4 }));
        later(8000, () => {
          event("CONFIRMED", 1);
          Object.assign(state, { phase: 0, exitDetected: false });
        });
        break;
      case "missed":
        event("MISSED", 2);
        break;
      case "blister":
        state.blisterPresent = false;
        event("BLOCKED", 1);
        break;
      case "failure":
        Object.assign(state, { phase: 7, calibrated: false });
        break;
      case "offline":
        offline = true;
        state.updatedAt = Date.now() - 45000;
        break;
      case "restore":
        timers.splice(0).forEach(clearTimeout);
        offline = false;
        Object.assign(state, {
          phase: 0,
          calibrated: true,
          blisterPresent: true,
          storageHealthy: true,
          exitDetected: false,
          servoOpen: false,
          updatedAt: Date.now(),
        });
    }
  };
  return {
    demo: true,
    simulate,
    email: () => (signedIn ? "admin@demo.test" : null),
    async signIn() {
      signedIn = true;
      listeners.forEach((fn) => fn(true));
    },
    async signOut() {
      signedIn = false;
      listeners.forEach((fn) => fn(false));
    },
    onSession(fn) {
      listeners.add(fn);
      fn(signedIn);
      return () => listeners.delete(fn);
    },
    listUsers: () => ok(users),
    devices() {
      if (!offline) state.updatedAt = Date.now();
      return ok(devices);
    },
    async setAccess(uid, enabled, expected) {
      const user = find(uid);
      const record = bump(user, expected, {
        enabled,
        revokedAt: enabled
          ? user.access.revokedAt
          : Math.floor(Date.now() / 1000),
      });
      user.disabled = !enabled;
      return record;
    },
    async setFeatures(uid, features, expected) {
      const user = find(uid);
      if (user.access.role !== "owner")
        throw new ApiError(409, "FEATURES_ONLY_FOR_OWNER");
      return bump(user, expected, {
        features: { ...user.access.features, ...features },
      });
    },
  };
}
