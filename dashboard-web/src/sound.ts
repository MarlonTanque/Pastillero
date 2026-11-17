/**
 * Alarmas sonoras con Web Audio: sin archivos externos. Los navegadores solo permiten sonido
 * después de una interacción, por eso `unlock()` se llama al iniciar sesión o al activar el sonido.
 */
type Ctor = typeof AudioContext;
let ctx: AudioContext | null = null;

function context(): AudioContext | null {
  const C: Ctor | undefined =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: Ctor }).webkitAudioContext;
  if (!C) return null;
  ctx ??= new C();
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

function tone(
  freq: number,
  start: number,
  duration: number,
  type: OscillatorType = "sine",
  volume = 0.18,
) {
  const c = context();
  if (!c) return;
  const t = c.currentTime + start,
    osc = c.createOscillator(),
    gain = c.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t);
  gain.gain.setValueAtTime(0.0001, t);
  gain.gain.exponentialRampToValueAtTime(volume, t + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, t + duration);
  osc.connect(gain).connect(c.destination);
  osc.start(t);
  osc.stop(t + duration + 0.05);
}

export const sounds = {
  unlock: () => void context(),
  /** Sirena de dos tonos para alertas críticas; se repite mientras no se reconozcan. */
  alarm() {
    [0, 0.5].forEach((s) => {
      tone(880, s, 0.24, "square", 0.12);
      tone(660, s + 0.25, 0.24, "square", 0.12);
    });
  },
  /** Dos pitidos cortos para advertencias. */
  warning() {
    tone(740, 0, 0.14, "triangle");
    tone(740, 0.2, 0.14, "triangle");
  },
  /** Tono ascendente para confirmar comandos y tomas. */
  success() {
    tone(523, 0, 0.12);
    tone(659, 0.11, 0.12);
    tone(784, 0.22, 0.2);
  },
};

const KEY = "badi-admin-sound";
export function loadMuted(): boolean {
  try {
    return localStorage.getItem(KEY) === "off";
  } catch {
    return false;
  }
}
export function saveMuted(muted: boolean) {
  try {
    localStorage.setItem(KEY, muted ? "off" : "on");
  } catch {
    /* Preferencia opcional. */
  }
}
