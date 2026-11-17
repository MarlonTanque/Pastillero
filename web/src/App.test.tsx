import { it, expect } from "vitest";
import {
  act,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { monday } from "./calendar";
import { preview } from "./preview";
const start = async () => {
  render(<App />);
  await screen.findByRole("heading", { level: 1 });
};
it("muestra el estado vacío sin fabricar entregas", async () => {
  await start();
  expect(
    screen.getByText("Comienza con tu primer medicamento"),
  ).toBeInTheDocument();
  expect(screen.getByText("Confirmaciones físicas")).toBeInTheDocument();
  expect(screen.getByText(/Vista web de demostración/)).toBeInTheDocument();
});
it("navega a un calendario con siete días reales", async () => {
  location.hash = "/calendar";
  await start();
  expect(screen.getByLabelText("Días de la semana").children).toHaveLength(7);
  await userEvent.click(screen.getByLabelText("Semana siguiente"));
  await waitFor(() =>
    expect(
      JSON.parse(localStorage.getItem("badi-preview")!).weekStart,
    ).toBeGreaterThan(+monday()),
  );
});
it("guarda un medicamento desde el formulario", async () => {
  location.hash = "/medications";
  await start();
  await userEvent.click(
    screen.getAllByRole("button", { name: "Agregar medicamento" })[0],
  );
  await userEvent.type(
    screen.getByLabelText("Nombre del medicamento"),
    "Pauta de ensayo",
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Guardar medicamento" }),
  );
  expect(
    await screen.findByRole("heading", { name: "Pauta de ensayo" }),
  ).toBeInTheDocument();
  expect(
    JSON.parse(localStorage.getItem("badi-preview")!).medications[0].times,
  ).toEqual(["08:00"]);
});
it("conserva un intervalo propio de la pauta", async () => {
  location.hash = "/medications";
  await start();
  await userEvent.click(
    screen.getAllByRole("button", { name: "Agregar medicamento" })[0],
  );
  await userEvent.type(
    screen.getByLabelText("Nombre del medicamento"),
    "Intervalo QA",
  );
  await userEvent.selectOptions(
    screen.getByLabelText("Tipo de horario"),
    "interval",
  );
  fireEvent.change(screen.getByLabelText(/^Intervalo en minutos/), {
    target: { value: "360" },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Guardar medicamento" }),
  );
  expect(await screen.findByText("Cada 360 minutos")).toBeInTheDocument();
});
it("cambia el tema y lo conserva", async () => {
  await start();
  await userEvent.click(screen.getByLabelText("Activar tema oscuro"));
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(localStorage.getItem("badi-theme")).toBe("dark");
});
it("permite cinco posiciones y explica el cero reservado", async () => {
  location.hash = "/settings";
  await start();
  await userEvent.selectOptions(
    screen.getByLabelText("Posiciones totales"),
    "5",
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Guardar ajustes" }),
  );
  await waitFor(() =>
    expect(
      JSON.parse(localStorage.getItem("badi-preview")!).settings.positions,
    ).toBe(5),
  );
  expect(screen.getByText(/El cero se conserva/)).toBeInTheDocument();
});
it("eliminar una pauta conserva el historial", async () => {
  const s = preview("snapshot", {});
  s.medications = [
    {
      id: "m",
      name: "Pauta eliminable",
      mode: "daily",
      times: ["08:00"],
      zoneId: "UTC",
      compartment: 1,
      intervalMinutes: 480,
      startAt: 1800000000000,
      endAt: 0,
      enabled: true,
    },
  ];
  s.events = [
    {
      id: "e",
      doseId: "d",
      medicationId: "m",
      type: "CONFIRMED",
      simulation: true,
      compartment: 1,
      scheduledAt: 1800000000000,
      actualAt: 1800000001000,
    },
  ];
  localStorage.setItem("badi-preview", JSON.stringify(s));
  location.hash = "/medications";
  await start();
  await userEvent.click(screen.getByLabelText("Eliminar Pauta eliminable"));
  await userEvent.click(screen.getByRole("button", { name: "Eliminar pauta" }));
  await waitFor(() =>
    expect(
      JSON.parse(localStorage.getItem("badi-preview")!).medications,
    ).toHaveLength(0),
  );
  expect(JSON.parse(localStorage.getItem("badi-preview")!).events).toHaveLength(
    1,
  );
});
it("la publicación en navegador no se presenta como Firebase", async () => {
  await start();
  await userEvent.click(
    screen.getByRole("button", { name: "Validar plan local" }),
  );
  expect(
    await screen.findByText("Vista web: no se publica en Firebase"),
  ).toBeInTheDocument();
});
it("el botón Atrás nativo cierra el formulario sin guardar una pauta", async () => {
  await start();
  await userEvent.click(
    screen.getByRole("button", { name: "Agregar medicamento" }),
  );
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  act(() => {
    expect(window.__badiBack?.()).toBe(true);
  });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(
    JSON.parse(localStorage.getItem("badi-preview")!).medications,
  ).toHaveLength(0);
  expect(window.__badiBack?.()).toBe(false);
});
it("la reconciliación conserva pautas locales solo tras elegir esa opción", async () => {
  const snapshot = {
    ...preview("snapshot", {}),
    authorized: true,
    signedIn: true,
  };
  const actions: string[] = [];
  window.BadiNative = {
    postMessage: (raw: string) => {
      const request = JSON.parse(raw);
      actions.push(request.action);
      queueMicrotask(() =>
        window.BadiNative?.onmessage?.({
          data: JSON.stringify({ id: request.id, ok: true, data: snapshot }),
        }),
      );
    },
  };
  location.hash = "/settings";
  await start();
  await userEvent.click(
    screen.getByRole("button", { name: "Revisar programa remoto" }),
  );
  expect(actions).not.toContain("rebase");
  await userEvent.click(
    screen.getByRole("button", { name: "Conservar pautas locales" }),
  );
  await waitFor(() => expect(actions).toContain("rebase"));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
});
it("oculta las funciones que el administrador deshabilitó", async () => {
  localStorage.setItem(
    "badi-preview",
    JSON.stringify({
      ...preview("snapshot", {}),
      features: { medications: false, publish: false, diagnostics: false },
    }),
  );
  location.hash = "/medications";
  await start();
  expect(
    screen.queryByRole("button", { name: "Agregar medicamento" }),
  ).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Validar plan local/ }),
  ).toBeDisabled();
  location.hash = "/settings";
  await act(async () =>
    window.dispatchEvent(new HashChangeEvent("hashchange")),
  );
  expect(
    screen.queryByRole("button", { name: "Comprobar conexión" }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Guardar ajustes" })).toBeEnabled();
});
