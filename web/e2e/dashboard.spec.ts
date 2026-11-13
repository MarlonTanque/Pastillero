import { test, expect } from "@playwright/test";
test("interfaz vacía, navegación, tema y calendario sin desbordamiento", async ({
  page,
}, info) => {
  const external: string[] = [];
  page.on("request", (r) => {
    if (!r.url().startsWith("http://127.0.0.1:4173")) external.push(r.url());
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Un día más, a tu ritmo." }),
  ).toBeVisible();
  await expect(
    page.getByText("Comienza con tu primer medicamento"),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `../reports/v2-${info.project.name}-home.png`,
    fullPage: true,
  });
  await page.getByLabel("Activar tema oscuro").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("link", { name: "Calendario", exact: true }).click();
  await expect(
    page.getByLabel("Días de la semana").locator("button"),
  ).toHaveCount(7);
  await page.getByLabel("Semana siguiente").click();
  await page.screenshot({
    path: `../reports/v2-${info.project.name}-calendar-dark.png`,
    fullPage: true,
  });
  expect(external).toEqual([]);
});
test("medicamento con horario, ajustes y persistencia de la vista local", async ({
  page,
}) => {
  await page.goto("/#/medications");
  await page
    .getByRole("button", { name: "Agregar medicamento" })
    .first()
    .click();
  await page
    .getByLabel("Nombre del medicamento")
    .fill("Pauta de prueba visual");
  await page
    .getByLabel("Horas (24 h, separadas por coma)")
    .fill("08:00, 20:00");
  await page.getByRole("button", { name: "Guardar medicamento" }).click();
  await expect(
    page.getByRole("heading", { name: "Pauta de prueba visual" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Pauta de prueba visual" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Ajustes", exact: true }).click();
  await page.getByLabel("Posiciones totales").selectOption("5");
  await page.getByRole("button", { name: "Guardar ajustes" }).click();
  await expect(page.getByLabel("Posiciones totales")).toHaveValue("5");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
test("reducción de movimiento y diálogo accesible", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: "Agregar medicamento" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(page.getByLabel("Nombre del medicamento")).toBeFocused();
  const duration = await dialog.evaluate(
    (x) => getComputedStyle(x).animationDuration,
  );
  expect(duration).toBe("0s");
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});
