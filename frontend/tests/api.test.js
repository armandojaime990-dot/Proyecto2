const { createApiClient } = require("../public/js/api.js");

function memoryStorage() {
  const data = {};
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
  };
}

function mockFetch(status, body) {
  return jest.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    json: () => Promise.resolve(body),
  });
}

describe("ApiClient", () => {
  test("login guarda token y usuario", async () => {
    const storage = memoryStorage();
    const fetch = mockFetch(200, { token: "abc", user: { id: 1, name: "Admin" } });
    const api = createApiClient(fetch, storage);

    const user = await api.login("a@b.com", "x");

    expect(user.name).toBe("Admin");
    expect(storage.getItem("token")).toBe("abc");
    expect(api.isAuthenticated()).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/auth/login", expect.objectContaining({ method: "POST" }));
  });

  test("envia el token Bearer en peticiones protegidas", async () => {
    const storage = memoryStorage();
    storage.setItem("token", "tkn");
    const fetch = mockFetch(200, { users: [] });
    await createApiClient(fetch, storage).listUsers();
    expect(fetch.mock.calls[0][1].headers.Authorization).toBe("Bearer tkn");
  });

  test("error 401 cierra la sesion", async () => {
    const storage = memoryStorage();
    storage.setItem("token", "viejo");
    const api = createApiClient(mockFetch(401, { error: "Token expirado" }), storage);
    await expect(api.listUsers()).rejects.toMatchObject({ status: 401 });
    expect(api.isAuthenticated()).toBe(false);
  });

  test("propaga errores de validacion del backend", async () => {
    const api = createApiClient(mockFetch(409, { error: "El email ya esta registrado", fields: { email: "Duplicado" } }), memoryStorage());
    await expect(api.createUser({})).rejects.toMatchObject({ status: 409, fields: { email: "Duplicado" } });
  });

  test("delete con 204 resuelve null", async () => {
    const fetch = jest.fn().mockResolvedValue({ status: 204, ok: true });
    await expect(createApiClient(fetch, memoryStorage()).deleteUser(5)).resolves.toBeNull();
    expect(fetch.mock.calls[0][0]).toBe("/api/users/5");
    expect(fetch.mock.calls[0][1].method).toBe("DELETE");
  });

  test("logout limpia el almacenamiento", () => {
    const storage = memoryStorage();
    storage.setItem("token", "t");
    storage.setItem("user", "{}");
    const api = createApiClient(mockFetch(200, {}), storage);
    api.logout();
    expect(api.currentUser()).toBeNull();
    expect(api.isAuthenticated()).toBe(false);
  });
});
