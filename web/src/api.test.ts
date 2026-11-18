import { it, expect, vi } from "vitest";
import { request } from "./api";
it("el puente envía JSON con versión y sin credenciales", async () => {
  let sent = "";
  window.BadiNative = {
    postMessage(text) {
      sent = text;
      const j = JSON.parse(text);
      queueMicrotask(() =>
        window.BadiNative?.onmessage?.({
          data: JSON.stringify({ id: j.id, ok: true, data: {} }),
        }),
      );
    },
  };
  await request("snapshot", { weekStart: 1800000000000 });
  const j = JSON.parse(sent);
  expect(j.version).toBe(1);
  expect(j.action).toBe("snapshot");
  expect(sent).not.toMatch(/password|idToken|apiKey/);
});
it("propaga un rechazo nativo al formulario", async () => {
  window.BadiNative = {
    postMessage(text) {
      const j = JSON.parse(text);
      queueMicrotask(() =>
        window.BadiNative?.onmessage?.({
          data: JSON.stringify({ id: j.id, ok: false, error: "No autorizado" }),
        }),
      );
    },
  };
  await expect(request("publish")).rejects.toThrow("No autorizado");
});
it("un mensaje corrupto no confirma la solicitud", async () => {
  vi.useFakeTimers();
  window.BadiNative = {
    postMessage() {
      window.BadiNative?.onmessage?.({ data: "invalid-json" });
    },
  };
  const p = request("snapshot");
  const assertion = expect(p).rejects.toThrow("Java no respondió");
  await vi.advanceTimersByTimeAsync(30001);
  await assertion;
  vi.useRealTimers();
});
it("la vista web no ofrece autenticación de Firebase", async () => {
  delete window.BadiNative;
  await expect(request("signIn")).rejects.toThrow("dentro del APK");
});

it("Wi-Fi en navegador no simula un aprovisionamiento real", async () => {
  delete window.BadiNative;
  await expect(request("wifiSetup")).rejects.toThrow("teléfono con Wi-Fi");
});
it("Wi-Fi solo abre una pantalla nativa sin transmitir credenciales", async () => {
  let sent = "";
  window.BadiNative = { postMessage(text) {
    sent = text;
    const j = JSON.parse(text);
    queueMicrotask(() => window.BadiNative?.onmessage?.({data: JSON.stringify({id:j.id,ok:true,data:{}})}));
  }};
  await request("wifiSetup");
  expect(JSON.parse(sent).payload).toEqual({});
  expect(sent).not.toMatch(/ssid|password|pop|credential/i);
});
