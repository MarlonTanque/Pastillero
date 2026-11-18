import type { Action, Snapshot } from "./types";
import { preview } from "./preview";
declare global {
  interface Window {
    BadiNative?: {
      postMessage: (text: string) => void;
      onmessage?: (e: { data: string }) => void;
    };
    __badiUpdate?: (text: string) => void;
    __badiBack?: () => boolean;
  }
}
interface Reply {
  id: string;
  ok: boolean;
  data: Snapshot;
  error?: string;
}
let counter = 0;
const pending = new Map<
  string,
  {
    resolve: (data: Snapshot) => void;
    reject: (e: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }
>();
const subscribers = new Set<(data: Snapshot) => void>();
export function listen(fn: (data: Snapshot) => void): () => void {
  subscribers.add(fn);
  return () => {
    subscribers.delete(fn);
  };
}
function update(data: Snapshot) {
  subscribers.forEach((fn) => fn(data));
}
window.__badiUpdate = (text) => {
  try {
    update(JSON.parse(text) as Snapshot);
  } catch {
    /* No interpretar un mensaje corrupto como estado confirmado. */
  }
};
export function request(
  action: Action,
  payload: Record<string, unknown> = {},
): Promise<Snapshot> {
  if (!window.BadiNative) {
    if (action === "wifiSetup") return Promise.reject(new Error("Usa la app Android en un teléfono con Wi-Fi; el navegador es una demostración."));
    try {
      const data = preview(action, payload);
      update(data);
      return Promise.resolve(data);
    } catch (e) {
      return Promise.reject(e);
    }
  }
  const bridge = window.BadiNative;
  bridge.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data) as Reply,
        item = pending.get(msg.id);
      if (!item) return;
      clearTimeout(item.timer);
      pending.delete(msg.id);
      if (msg.ok) {
        if (msg.data?.medications) update(msg.data);
        item.resolve(msg.data);
      } else
        item.reject(
          new Error(msg.error || "No se pudo completar la operación."),
        );
    } catch {
      /* La validación nativa sigue siendo la autoridad. */
    }
  };
  const id = `web-${Date.now()}-${++counter}`;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error("Java no respondió; vuelve a intentar."));
    }, 30000);
    pending.set(id, { resolve, reject, timer });
    bridge.postMessage(JSON.stringify({ version: 1, id, action, payload }));
  });
}
