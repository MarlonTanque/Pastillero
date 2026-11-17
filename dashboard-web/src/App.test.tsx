import { it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { demoApi } from "./demo";
import { ApiError, call } from "./api";

const start = async () => {
  const api = demoApi();
  render(<App api={api} />);
  await userEvent.click(
    await screen.findByRole("button", { name: "Entrar a la demostración" }),
  );
  await screen.findByText("responsable@demo.test");
  return api;
};
const card = (email: string) =>
  screen.getByRole("heading", { name: email }).closest("article")!;

it("bloquea y permite funciones del responsable con control de versión", async () => {
  const api = await start();
  const sw = screen.getByRole("switch", {
    name: "Publicar al pastillero para responsable@demo.test",
  });
  expect(sw).toBeChecked();
  await userEvent.click(sw);
  expect(
    await screen.findByText("Publicar al pastillero: bloqueado"),
  ).toBeInTheDocument();
  expect(sw).not.toBeChecked();
  const owner = (await api.listUsers()).find(
    (u) => u.uid === "responsable-demo",
  )!;
  expect(owner.access?.features).toEqual({
    diagnostics: false,
    publish: false,
  });
  expect(owner.access?.version).toBe(4);
  // El diagnóstico venía bloqueado en los datos de ejemplo.
  expect(
    screen.getByRole("switch", {
      name: "Diagnóstico y vista clásica para responsable@demo.test",
    }),
  ).not.toBeChecked();
});

it("no ofrece funciones de la app para el ESP32 ni para el administrador", async () => {
  await start();
  expect(within(card("esp32@demo.test")).queryAllByRole("switch")).toHaveLength(
    0,
  );
  expect(
    within(card("esp32@demo.test")).getByText(/no usa la app/),
  ).toBeInTheDocument();
  expect(within(card("admin@demo.test")).queryAllByRole("button")).toHaveLength(
    0,
  );
});

it("pide confirmación antes de bloquear una cuenta", async () => {
  await start();
  const owner = card("responsable@demo.test");
  await userEvent.click(
    within(owner).getByRole("button", { name: "Bloquear cuenta" }),
  );
  const dialog = screen.getByRole("dialog");
  await userEvent.click(
    within(dialog).getByRole("button", { name: "Cancelar" }),
  );
  expect(within(owner).getByText("Activa")).toBeInTheDocument();
  await userEvent.click(
    within(owner).getByRole("button", { name: "Bloquear cuenta" }),
  );
  await userEvent.click(
    within(screen.getByRole("dialog")).getByRole("button", {
      name: "Bloquear",
    }),
  );
  expect(await within(owner).findByText("Bloqueada")).toBeInTheDocument();
  // Con la cuenta bloqueada los interruptores quedan inactivos hasta habilitarla.
  within(owner)
    .getAllByRole("switch")
    .forEach((s) => expect(s).toBeDisabled());
});

it("muestra el carrusel con el cero vacío y cuatro compartimentos", async () => {
  await start();
  await userEvent.click(screen.getByRole("button", { name: "Dispositivos" }));
  expect(
    screen.getByRole("img", {
      name: "5 posiciones; cero reservado al retorno",
    }),
  ).toBeInTheDocument();
  expect(screen.getByText("pastillero-01")).toBeInTheDocument();
  expect(screen.getByText("En espera")).toBeInTheDocument();
  expect(
    screen.getByText(/Responsable: responsable@demo.test/),
  ).toBeInTheDocument();
});

it("envía el token como Bearer y traduce los errores del backend", async () => {
  const fetch = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ error: "VERSION_CONFLICT" }), {
      status: 409,
    }),
  );
  vi.stubGlobal("fetch", fetch);
  await expect(
    call(async () => "token-1", "PATCH", "/api/users/u1/features", {
      features: { publish: false },
      expectedVersion: 1,
    }),
  ).rejects.toEqual(new ApiError(409, "VERSION_CONFLICT"));
  expect(fetch.mock.calls[0][1].headers.Authorization).toBe("Bearer token-1");
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
    features: { publish: false },
    expectedVersion: 1,
  });
  vi.unstubAllGlobals();
});

it("muestra la alarma, la reconoce y confirma cuando se resuelve", async () => {
  const api = await start();
  await userEvent.click(screen.getByRole("button", { name: "Dispositivos" }));
  api.simulate!("blister");
  api.simulate!("failure");
  await userEvent.click(screen.getByRole("button", { name: "Actualizar" }));
  const banner = await screen.findByRole("alert");
  expect(banner).toHaveTextContent("Fallo: entregas detenidas");
  expect(banner).toHaveTextContent("más");
  expect(screen.getByText("Entrega bloqueada · C1")).toBeInTheDocument();
  expect(screen.getByLabelText(/sin reconocer/)).toBeInTheDocument();
  expect(document.querySelector(".device.flashing")).not.toBeNull();
  // Reconocer todas detiene la alarma, pero las condiciones siguen visibles.
  await userEvent.click(screen.getByRole("button", { name: /^Alertas/ }));
  await userEvent.click(
    screen.getByRole("button", { name: "Reconocer todas" }),
  );
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.getAllByText("Reconocida").length).toBeGreaterThan(0);
  api.simulate!("restore");
  await userEvent.click(screen.getByRole("button", { name: "Actualizar" }));
  expect(
    await screen.findByText(
      "✅ Todo en orden: ningún sensor reporta problemas.",
    ),
  ).toBeInTheDocument();
  expect(
    screen.getAllByText("Resuelto: Fallo: entregas detenidas").length,
  ).toBeGreaterThan(0);
});
