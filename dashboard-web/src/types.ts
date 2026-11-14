export type Feature =
  "medications" | "publish" | "deviceSettings" | "diagnostics";

/** Registro access/users/UID. Solo el backend administrativo lo escribe. */
export interface AccessRecord {
  role: "owner" | "device";
  enabled: boolean;
  version: number;
  revokedAt: number;
  features?: Partial<Record<Feature, boolean>>;
  updatedAt?: number;
  updatedBy?: string;
}
export interface AdminUser {
  uid: string;
  email: string | null;
  disabled: boolean;
  protected: boolean;
  access: AccessRecord | null;
}
export interface Regimen {
  id: string;
  name: string;
  mode: "daily" | "interval";
  times?: string[];
  intervalMinutes?: number;
  compartment: number;
  zoneId?: string;
  enabled: boolean;
}
export interface DeviceEvent {
  doseId: string;
  type: string;
  scheduledAt: number;
  actualAt: number;
  compartment: number;
  simulation: boolean;
  medicationId?: string;
}
export interface DeviceState {
  phase?: number;
  calibrated?: boolean;
  appliedRevision?: number;
  updatedAt?: number;
  simulation?: boolean;
  storageHealthy?: boolean;
  blisterPresent?: boolean;
  positions?: number;
}
export interface Device {
  ownerUid?: string;
  deviceUid?: string;
  v2?: {
    program?: {
      revision?: number;
      positions?: number;
      targetMode?: string;
      regimens?: Record<string, Regimen>;
    };
    state?: DeviceState;
    events?: Record<string, DeviceEvent>;
  };
}
export type Devices = Record<string, Device>;
