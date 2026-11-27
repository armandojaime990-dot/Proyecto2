// Casos parametrizados de la API (Backend) via Playwright
const { test, expect } = require("@playwright/test");
const { ADMIN, apiToken, uniqueEmail } = require("./helpers");

const PROTECTED = [
  ["GET", "/api/users"], ["GET", "/api/users/1"], ["POST", "/api/users"],
  ["PUT", "/api/users/1"], ["DELETE", "/api/users/1"], ["GET", "/api/auth/me"],
];

test.describe("API - acceso no autorizado", () => {
  for (const [method, url] of PROTECTED) {
    test(`${method} ${url} sin token -> 401`, async ({ request }) => {
      const res = await request.fetch(url, { method, data: {} });
      expect(res.status()).toBe(401);
    });
    test(`${method} ${url} con token falso -> 401`, async ({ request }) => {
      const res = await request.fetch(url, { method, data: {}, headers: { Authorization: "Bearer falso.token.jwt" } });
      expect(res.status()).toBe(401);
    });
  }
});

const BAD_LOGINS = [
  [{}, 400], [{ email: ADMIN.email }, 400], [{ password: ADMIN.password }, 400], [{ email: "", password: "" }, 400],
  [{ email: ADMIN.email, password: "mal" }, 401], [{ email: ADMIN.email, password: ADMIN.password.toLowerCase() }, 401],
  [{ email: "noexiste@test.com", password: ADMIN.password }, 401], [{ email: ADMIN.email, password: " " + ADMIN.password }, 401],
];

test.describe("API - login invalido", () => {
  for (const [data, status] of BAD_LOGINS) {
    test(`login ${JSON.stringify(data)} -> ${status}`, async ({ request }) => {
      expect((await request.post("/api/auth/login", { data })).status()).toBe(status);
    });
  }
  test("login con email en mayusculas funciona", async ({ request }) => {
    const res = await request.post("/api/auth/login", { data: { ...ADMIN, email: ADMIN.email.toUpperCase() } });
    expect(res.status()).toBe(200);
  });
});

const INVALID_CREATE = [
  { email: "a@b.com", password: "secreto1" }, { name: "Ana", password: "secreto1" }, { name: "Ana", email: "a@b.com" },
  { name: "A", email: "a@b.com", password: "secreto1" }, { name: "Ana", email: "malo", password: "secreto1" },
  { name: "Ana", email: "a@b.com", password: "123" }, { name: "Ana", email: "a@b.com", password: "secreto1", role: "root" },
  {}, { name: "", email: "", password: "" }, { name: "Ana", email: "a@b", password: "secreto1" },
];

test.describe("API - validaciones al crear", () => {
  let headers;
  test.beforeEach(async ({ request }) => { headers = { Authorization: `Bearer ${await apiToken(request)}` }; });
  for (const data of INVALID_CREATE) {
    test(`crear ${JSON.stringify(data)} -> 400`, async ({ request }) => {
      const res = await request.post("/api/users", { headers, data });
      expect(res.status()).toBe(400);
      expect(Object.keys((await res.json()).fields).length).toBeGreaterThan(0);
    });
  }
});

const MISSING = [999999, 888888, 777777, 2147483647];

test.describe("API - recursos inexistentes", () => {
  let headers;
  test.beforeEach(async ({ request }) => { headers = { Authorization: `Bearer ${await apiToken(request)}` }; });
  for (const id of MISSING) {
    test(`GET /api/users/${id} -> 404`, async ({ request }) => {
      expect((await request.get(`/api/users/${id}`, { headers })).status()).toBe(404);
    });
    test(`PUT /api/users/${id} -> 404`, async ({ request }) => {
      expect((await request.put(`/api/users/${id}`, { headers, data: { name: "Nadie" } })).status()).toBe(404);
    });
    test(`DELETE /api/users/${id} -> 404`, async ({ request }) => {
      expect((await request.delete(`/api/users/${id}`, { headers })).status()).toBe(404);
    });
  }
});

test.describe("API - CRUD por rol y campos", () => {
  let headers;
  test.beforeEach(async ({ request }) => { headers = { Authorization: `Bearer ${await apiToken(request)}` }; });

  for (const role of ["user", "admin"]) {
    test(`usuario con rol ${role} puede iniciar sesion`, async ({ request }) => {
      const email = uniqueEmail(role);
      await request.post("/api/users", { headers, data: { name: `Rol ${role}`, email, password: "secreto1", role } });
      const res = await request.post("/api/auth/login", { data: { email, password: "secreto1" } });
      expect(res.status()).toBe(200);
      expect((await res.json()).user.role).toBe(role);
    });
  }

  const UPDATES = [{ name: "Nuevo Nombre" }, { role: "admin" }, { email: "CAMBIO" }, { password: "otraClave1" }];
  for (const change of UPDATES) {
    test(`actualizar ${Object.keys(change)[0]}`, async ({ request }) => {
      const email = uniqueEmail("upd");
      const { user } = await (await request.post("/api/users", {
        headers, data: { name: "Para Editar", email, password: "secreto1", role: "user" },
      })).json();
      const data = change.email ? { email: uniqueEmail("nuevo") } : change;
      const res = await request.put(`/api/users/${user.id}`, { headers, data });
      expect(res.status()).toBe(200);
      if (change.password) {
        expect((await request.post("/api/auth/login", { data: { email, password: change.password } })).status()).toBe(200);
      } else {
        const [field, value] = Object.entries(data)[0];
        expect((await res.json()).user[field]).toBe(field === "email" ? value.toLowerCase() : value);
      }
      await request.delete(`/api/users/${user.id}`, { headers });
    });
  }

  for (const variant of ["upper", "mixed", "spaces"]) {
    test(`email duplicado (${variant}) -> 409`, async ({ request }) => {
      const email = uniqueEmail("dup");
      const other = variant === "upper" ? email.toUpperCase() : variant === "mixed" ? email[0].toUpperCase() + email.slice(1) : `  ${email}  `;
      await request.post("/api/users", { headers, data: { name: "Uno", email, password: "secreto1" } });
      expect((await request.post("/api/users", { headers, data: { name: "Dos", email: other, password: "secreto1" } })).status()).toBe(409);
    });
  }

  test("no se puede eliminar al propio usuario -> 400", async ({ request }) => {
    const me = (await (await request.get("/api/auth/me", { headers })).json()).user;
    expect((await request.delete(`/api/users/${me.id}`, { headers })).status()).toBe(400);
  });

  test("GET /api/health incluye version", async ({ request }) => {
    expect((await (await request.get("/api/health")).json()).version).toBeTruthy();
  });
});
