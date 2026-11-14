import { ApiError, type AdminApi } from "./api";
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
  return {
    demo: true,
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
    devices: () => ok(devices),
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
