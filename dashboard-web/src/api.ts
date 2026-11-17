import type { AccessRecord, AdminUser, Devices, Feature } from "./types";

/** Escenarios que la demostración puede provocar para mostrar las alertas. */
export type SimKind =
  "deliver" | "missed" | "blister" | "failure" | "offline" | "restore";

/** Operaciones del backend administrativo (docs/ADMINISTRACION_WEB.md). */
export interface AdminApi {
  /** Solo en demostración: altera el pastillero ficticio. */
  simulate?(kind: SimKind): void;
  readonly demo: boolean;
  email(): string | null;
  signIn(email: string, password: string): Promise<void>;
  signOut(): Promise<void>;
  onSession(fn: (signedIn: boolean) => void): () => void;
  listUsers(): Promise<AdminUser[]>;
  devices(): Promise<Devices>;
  setAccess(
    uid: string,
    enabled: boolean,
    expectedVersion: number,
  ): Promise<AccessRecord>;
  setFeatures(
    uid: string,
    features: Partial<Record<Feature, boolean>>,
    expectedVersion: number,
  ): Promise<AccessRecord>;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

/** Cliente HTTP: envía el ID token de Firebase; la autorización real la decide el backend. */
export async function call<T>(
  token: () => Promise<string>,
  method: "GET" | "PATCH",
  path: string,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        Authorization: `Bearer ${await token()}`,
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "SERVICE_UNAVAILABLE");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new ApiError(response.status, data.error ?? "SERVICE_UNAVAILABLE");
  return data as T;
}
