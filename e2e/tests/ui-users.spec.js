// Pruebas del FRONTEND: CRUD de usuarios desde la interfaz
const { test, expect } = require("@playwright/test");
const { uiLogin, uniqueEmail } = require("./helpers");

test.describe("UI - CRUD usuarios", () => {
  test.beforeEach(async ({ page }) => {
    await uiLogin(page);
  });

  test("lista usuarios (incluye al admin)", async ({ page }) => {
    await expect(page.getByTestId("user-row").first()).toBeVisible();
  });

  test("validaciones del formulario de nuevo usuario", async ({ page }) => {
    await page.getByTestId("new-user").click();
    await page.getByTestId("save").click();
    await expect(page.getByTestId("error-name")).not.toBeEmpty();
    await expect(page.getByTestId("error-email")).toHaveText("Email invalido");
    await expect(page.getByTestId("error-password")).not.toBeEmpty();
  });

  test("crear, editar y eliminar un usuario", async ({ page }) => {
    const email = uniqueEmail("ui");

    // Crear
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("Usuario UI");
    await page.getByTestId("field-email").fill(email);
    await page.getByTestId("field-password").fill("secreto1");
    await page.getByTestId("field-role").selectOption("user");
    await page.getByTestId("save").click();
    await expect(page.getByTestId("flash")).toHaveText("Usuario creado");
    const row = page.locator(`[data-testid=user-row][data-email="${email}"]`);
    await expect(row).toContainText("Usuario UI");

    // Editar
    await row.getByRole("button", { name: "Editar" }).click();
    await expect(page.getByTestId("modal-title")).toHaveText("Editar usuario");
    await page.getByTestId("field-name").fill("Usuario UI Editado");
    await page.getByTestId("field-role").selectOption("admin");
    await page.getByTestId("save").click();
    await expect(page.getByTestId("flash")).toHaveText("Usuario actualizado");
    await expect(row).toContainText("Usuario UI Editado");
    await expect(row).toContainText("admin");

    // Eliminar
    await row.getByRole("button", { name: "Eliminar" }).click();
    await expect(page.getByTestId("confirm-text")).toContainText(email);
    await page.getByTestId("confirm-yes").click();
    await expect(page.getByTestId("flash")).toHaveText("Usuario eliminado");
    await expect(row).toHaveCount(0);
  });

  test("email duplicado muestra error del servidor", async ({ page }) => {
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("Duplicado");
    await page.getByTestId("field-email").fill(process.env.E2E_ADMIN_EMAIL || "admin@demo.com");
    await page.getByTestId("field-password").fill("secreto1");
    await page.getByTestId("save").click();
    await expect(page.getByTestId("form-error")).toHaveText("El email ya esta registrado");
  });
});
