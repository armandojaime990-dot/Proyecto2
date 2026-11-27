// CRUD de usuarios via API (Backend)
const { test, expect } = require("@playwright/test");
const { apiToken, uniqueEmail } = require("./helpers");

test.describe("API - CRUD usuarios", () => {
  let headers;

  test.beforeEach(async ({ request }) => {
    headers = { Authorization: `Bearer ${await apiToken(request)}` };
  });

  test("ciclo completo: crear, leer, actualizar y eliminar", async ({ request }) => {
    const email = uniqueEmail("api");

    const created = await request.post("/api/users", {
      headers,
      data: { name: "Usuario API", email, password: "secreto1", role: "user" },
    });
    expect(created.status()).toBe(201);
    const { user } = await created.json();

    const read = await request.get(`/api/users/${user.id}`, { headers });
    expect(read.status()).toBe(200);
    expect((await read.json()).user.email).toBe(email);

    const list = await request.get("/api/users", { headers });
    expect((await list.json()).users.some((u) => u.id === user.id)).toBeTruthy();

    const updated = await request.put(`/api/users/${user.id}`, { headers, data: { name: "Usuario Editado" } });
    expect(updated.status()).toBe(200);
    expect((await updated.json()).user.name).toBe("Usuario Editado");

    const del = await request.delete(`/api/users/${user.id}`, { headers });
    expect(del.status()).toBe(204);
    expect((await request.get(`/api/users/${user.id}`, { headers })).status()).toBe(404);
  });

  test("crear con datos invalidos devuelve 400", async ({ request }) => {
    const res = await request.post("/api/users", { headers, data: { name: "A", email: "malo", password: "1" } });
    expect(res.status()).toBe(400);
  });

  test("crear con email duplicado devuelve 409", async ({ request }) => {
    const email = uniqueEmail("dup");
    const data = { name: "Duplicado", email, password: "secreto1", role: "user" };
    expect((await request.post("/api/users", { headers, data })).status()).toBe(201);
    expect((await request.post("/api/users", { headers, data })).status()).toBe(409);
  });
});
