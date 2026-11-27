// Pruebas del FRONTEND: pantalla de login
const { test, expect } = require("@playwright/test");
const { ADMIN, uiLogin } = require("./helpers");

test.describe("UI - Login", () => {
  test("muestra el formulario de login", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("login-title")).toHaveText("Gestión de Usuarios");
    await expect(page.getByTestId("login-email")).toBeVisible();
    await expect(page.getByTestId("login-password")).toBeVisible();
    await expect(page.getByTestId("login-submit")).toHaveText("Entrar");
  });

  test("valida campos vacios sin llamar al servidor", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("error-email")).toHaveText("El email es obligatorio");
    await expect(page.getByTestId("error-password")).toHaveText("La contrasena es obligatoria");
  });

  test("credenciales incorrectas muestran error", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("login-email").fill(ADMIN.email);
    await page.getByTestId("login-password").fill("incorrecta");
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("login-error")).toHaveText("Credenciales invalidas");
  });

  test("login correcto redirige a usuarios y permite cerrar sesion", async ({ page }) => {
    await uiLogin(page);
    await expect(page.getByTestId("users-title")).toHaveText("Usuarios");
    await expect(page.getByTestId("current-user")).toContainText("admin");
    await page.getByTestId("logout").click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("sin sesion /users.html redirige al login", async ({ page }) => {
    await page.goto("/users.html");
    await expect(page.getByTestId("login-title")).toBeVisible();
  });
});
