// Casos parametrizados de la interfaz (Frontend) via Playwright
const { test, expect } = require("@playwright/test");
const { ADMIN, uiLogin, uniqueEmail } = require("./helpers");

const LOGIN_EMAIL_ERRORS = [
  ["", "El email es obligatorio"], ["   ", "El email es obligatorio"], ["ana", "Email invalido"],
  ["ana@", "Email invalido"], ["@test.com", "Email invalido"], ["ana@test", "Email invalido"],
  ["ana test@x.com", "Email invalido"], ["ana@@test.com", "Email invalido"],
];

test.describe("UI - validacion del email en login", () => {
  for (const [email, message] of LOGIN_EMAIL_ERRORS) {
    test(`email "${email}" muestra "${message}"`, async ({ page }) => {
      await page.goto("/");
      await page.getByTestId("login-email").fill(email);
      await page.getByTestId("login-password").fill("algo");
      await page.getByTestId("login-submit").click();
      await expect(page.getByTestId("error-email")).toHaveText(message);
      await expect(page).toHaveURL(/\/$/);
    });
  }
});

const WRONG_PASSWORDS = ["incorrecta", ADMIN.password.toLowerCase(), ADMIN.password + "x"];

test.describe("UI - contrasenas incorrectas", () => {
  for (const password of WRONG_PASSWORDS) {
    test(`password "${password}" es rechazada`, async ({ page }) => {
      await page.goto("/");
      await page.getByTestId("login-email").fill(ADMIN.email);
      await page.getByTestId("login-password").fill(password);
      await page.getByTestId("login-submit").click();
      await expect(page.getByTestId("login-error")).toHaveText("Credenciales invalidas");
    });
  }
});

const FORM_ERRORS = [
  [{ name: "A" }, "name", "El nombre debe tener al menos 2 caracteres"],
  [{ name: "   " }, "name", "El nombre debe tener al menos 2 caracteres"],
  [{ email: "malo" }, "email", "Email invalido"],
  [{ email: "a@b" }, "email", "Email invalido"],
  [{ email: "sin arroba.com" }, "email", "Email invalido"],
  [{ password: "123" }, "password", "La contrasena debe tener al menos 6 caracteres"],
  [{ password: "12345" }, "password", "La contrasena debe tener al menos 6 caracteres"],
  [{ password: "" }, "password", "La contrasena debe tener al menos 6 caracteres"],
];

test.describe("UI - validaciones del formulario de usuario", () => {
  test.beforeEach(async ({ page }) => { await uiLogin(page); });

  for (const [override, field, message] of FORM_ERRORS) {
    test(`${field}=${JSON.stringify(Object.values(override)[0])} muestra error`, async ({ page }) => {
      const data = { name: "Valido", email: uniqueEmail("form"), password: "secreto1", ...override };
      await page.getByTestId("new-user").click();
      await page.getByTestId("field-name").fill(data.name);
      await page.getByTestId("field-email").fill(data.email);
      await page.getByTestId("field-password").fill(data.password);
      await page.getByTestId("save").click();
      await expect(page.getByTestId(`error-${field}`)).toHaveText(message);
      await expect(page.getByTestId("user-modal")).toBeVisible();
    });
  }
});

test.describe("UI - flujos del CRUD", () => {
  test.beforeEach(async ({ page }) => { await uiLogin(page); });

  for (const role of ["user", "admin"]) {
    test(`crear usuario con rol ${role} y verlo en la tabla`, async ({ page }) => {
      const email = uniqueEmail(`ui-${role}`);
      await page.getByTestId("new-user").click();
      await page.getByTestId("field-name").fill(`Rol ${role}`);
      await page.getByTestId("field-email").fill(email);
      await page.getByTestId("field-password").fill("secreto1");
      await page.getByTestId("field-role").selectOption(role);
      await page.getByTestId("save").click();
      const row = page.locator(`[data-testid=user-row][data-email="${email}"]`);
      await expect(row).toContainText(role);
      await row.getByRole("button", { name: "Eliminar" }).click();
      await page.getByTestId("confirm-yes").click();
      await expect(row).toHaveCount(0);
    });
  }

  test("cancelar el formulario no crea el usuario", async ({ page }) => {
    const email = uniqueEmail("cancel");
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("Cancelado");
    await page.getByTestId("field-email").fill(email);
    await page.getByTestId("cancel").click();
    await expect(page.getByTestId("user-modal")).toBeHidden();
    await expect(page.locator(`[data-testid=user-row][data-email="${email}"]`)).toHaveCount(0);
  });

  test("cancelar la eliminacion conserva el usuario", async ({ page }) => {
    const email = uniqueEmail("keep");
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("Conservar");
    await page.getByTestId("field-email").fill(email);
    await page.getByTestId("field-password").fill("secreto1");
    await page.getByTestId("save").click();
    const row = page.locator(`[data-testid=user-row][data-email="${email}"]`);
    await row.getByRole("button", { name: "Eliminar" }).click();
    await page.getByTestId("confirm-no").click();
    await expect(row).toHaveCount(1);
  });

  test("editar sin cambiar la contrasena la conserva", async ({ page, request }) => {
    const email = uniqueEmail("pwd");
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("Clave Fija");
    await page.getByTestId("field-email").fill(email);
    await page.getByTestId("field-password").fill("secreto1");
    await page.getByTestId("save").click();
    const row = page.locator(`[data-testid=user-row][data-email="${email}"]`);
    await row.getByRole("button", { name: "Editar" }).click();
    await expect(page.getByTestId("pwd-hint")).toContainText("dejar vacía");
    await page.getByTestId("field-name").fill("Clave Fija Editada");
    await page.getByTestId("save").click();
    await expect(row).toContainText("Clave Fija Editada");
    const res = await request.post("/api/auth/login", { data: { email, password: "secreto1" } });
    expect(res.status()).toBe(200);
  });

  test("el formulario de edicion se llena con los datos actuales", async ({ page }) => {
    await page.locator("[data-testid=user-row]").first().getByRole("button", { name: "Editar" }).click();
    await expect(page.getByTestId("modal-title")).toHaveText("Editar usuario");
    await expect(page.getByTestId("field-email")).not.toHaveValue("");
    await expect(page.getByTestId("field-name")).not.toHaveValue("");
  });

  test("cerrar sesion borra el token", async ({ page }) => {
    await page.getByTestId("logout").click();
    expect(await page.evaluate(() => localStorage.getItem("token"))).toBeNull();
    await page.goto("/users.html");
    await expect(page.getByTestId("login-title")).toBeVisible();
  });

  test("con sesion activa el login redirige a usuarios", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/users.html");
    await expect(page.getByTestId("users-title")).toBeVisible();
  });

  test("token invalido en el navegador manda al login", async ({ page }) => {
    await page.evaluate(() => localStorage.setItem("token", "token-roto"));
    await page.reload();
    await expect(page.getByTestId("login-title")).toBeVisible();
  });

  test("la tabla muestra columnas ID, Nombre, Email, Rol y Acciones", async ({ page }) => {
    await expect(page.locator("thead th")).toHaveText(["ID", "Nombre", "Email", "Rol", "Acciones"]);
  });

  test("los nombres con HTML se muestran como texto (sin XSS)", async ({ page }) => {
    const email = uniqueEmail("xss");
    await page.getByTestId("new-user").click();
    await page.getByTestId("field-name").fill("<b>negrita</b>");
    await page.getByTestId("field-email").fill(email);
    await page.getByTestId("field-password").fill("secreto1");
    await page.getByTestId("save").click();
    const row = page.locator(`[data-testid=user-row][data-email="${email}"]`);
    await expect(row).toContainText("<b>negrita</b>");
    await expect(row.locator("b")).toHaveCount(0);
  });
});
