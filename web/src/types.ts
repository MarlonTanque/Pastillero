export type View = "home" | "calendar" | "medications" | "history" | "settings";
export interface Medication {
  id: string;
  name: string;
  mode: "daily" | "interval";
  times: string[];
  zoneId: string;
  compartment: number;
  intervalMinutes: number;
  startAt: number;
  endAt: number;
  enabled: boolean;
}
export interface Settings {
  positions: 4 | 5;
  horizonDays: number;
  pumpDurationMs: number;
  ledEnabled: boolean;
  buzzerEnabled: boolean;
  lcdEnabled: boolean;
  exitSensorEnabled: boolean;
  servoEnabled: boolean;
  pumpEnabled: boolean;
}
export interface Occurrence {
  id: string;
  medicationId: string;
  name: string;
  scheduledAt: number;
  compartment: number;
}
export interface DoseEvent {
  id: string;
  doseId: string;
  medicationId: string;
  type: string;
  scheduledAt: number;
  actualAt: number;
  compartment: number;
  simulation: boolean;
}
export interface Snapshot {
  medications: Medication[];
  occurrences: Occurrence[];
  events: DoseEvent[];
  settings: Settings;
  device: {
    phase?: number;
    updatedAt?: number;
    calibrated?: boolean;
    positions?: number;
    appliedRevision?: number;
    exitDetected?: boolean;
  };
  signedIn: boolean;
  authorized: boolean;
  simulation: boolean;
  connection: string;
  programStatus: string;
  revision: number;
  pending: boolean;
  now: number;
  weekStart: number;
  pingStatus?: string;
  preview?: boolean;
}
export type Action =
  | "snapshot"
  | "saveMedication"
  | "deleteMedication"
  | "savePreferences"
  | "publish"
  | "retry"
  | "reload"
  | "rebase"
  | "ping"
  | "signIn"
  | "signOut"
  | "nativeView"
  | "wifiSetup";
export const defaults: Settings = {
  positions: 5,
  horizonDays: 7,
  pumpDurationMs: 2000,
  ledEnabled: true,
  buzzerEnabled: true,
  lcdEnabled: false,
  exitSensorEnabled: false,
  servoEnabled: false,
  pumpEnabled: false,
};
