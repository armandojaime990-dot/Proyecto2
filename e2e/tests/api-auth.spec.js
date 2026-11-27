// Pruebas del BACKEND (API REST) a traves del proxy nginx
const { test, expect } = require("@playwright/test");
const { ADMIN } = require("./helpers");

test.describe("API - autenticacion", () => {
  test("GET /api/health responde 200", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.status()).toBe(200);
    expect((await res.json()).status).toBe("ok");
  });

  test("POST /api/auth/login con credenciales validas devuelve token", async ({ request }) => {
    const res = await request.post("/api/auth/login", { data: ADMIN });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.token).toBeTruthy();
    expect(body.user.email).toBe(ADMIN.email);
  });

  test("POST /api/auth/login con contrasena incorrecta devuelve 401", async ({ request }) => {
    const res = await request.post("/api/auth/login", { data: { email: ADMIN.email, password: "incorrecta" } });
    expect(res.status()).toBe(401);
  });

  test("rutas protegidas sin token devuelven 401", async ({ request }) => {
    expect((await request.get("/api/users")).status()).toBe(401);
    expect((await request.get("/api/auth/me")).status()).toBe(401);
  });
});
