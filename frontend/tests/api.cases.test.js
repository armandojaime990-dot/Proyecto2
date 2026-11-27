// Casos parametrizados del cliente de la API
const { createApiClient } = require("../public/js/api.js");

function memoryStorage(token) {
  const data = token ? { token } : {};
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
  };
}

function mockFetch(status, body) {
  return jest.fn().mockResolvedValue({ status, ok: status >= 200 && status < 300, json: () => Promise.resolve(body) });
}

const CALLS = [
  ["listUsers", [], "GET", "/api/users", undefined, { users: [] }],
  ["me", [], "GET", "/api/auth/me", undefined, { user: {} }],
  ["createUser", [{ name: "A" }], "POST", "/api/users", { name: "A" }, { user: {} }],
  ["updateUser", [7, { name: "B" }], "PUT", "/api/users/7", { name: "B" }, { user: {} }],
  ["deleteUser", [9], "DELETE", "/api/users/9", undefined, {}],
];

test.each(CALLS)("%s usa el metodo y URL correctos", async (fn, args, method, url, body, response) => {
  const fetch = mockFetch(200, response);
  await createApiClient(fetch, memoryStorage("t"))[fn](...args);
  expect(fetch.mock.calls[0][0]).toBe(url);
  expect(fetch.mock.calls[0][1].method).toBe(method);
  expect(fetch.mock.calls[0][1].body).toBe(body === undefined ? undefined : JSON.stringify(body));
});

test.each(CALLS)("%s envia el token Bearer", async (fn, args, m, u, b, response) => {
  const fetch = mockFetch(200, response);
  await createApiClient(fetch, memoryStorage("mi-token"))[fn](...args);
  expect(fetch.mock.calls[0][1].headers.Authorization).toBe("Bearer mi-token");
});

const ERRORS = [400, 403, 404, 409, 500];

test.each(ERRORS)("listUsers propaga el error HTTP %i", async (status) => {
  const api = createApiClient(mockFetch(status, { error: "Fallo " + status }), memoryStorage("t"));
  await expect(api.listUsers()).rejects.toMatchObject({ status, message: "Fallo " + status });
});

test.each(ERRORS)("createUser propaga el error HTTP %i sin cerrar sesion", async (status) => {
  const storage = memoryStorage("t");
  const api = createApiClient(mockFetch(status, { error: "E" }), storage);
  await expect(api.createUser({})).rejects.toMatchObject({ status });
  expect(api.isAuthenticated()).toBe(true);
});

test.each(["listUsers", "me", "deleteUser", "createUser", "updateUser"])("%s con 401 cierra la sesion", async (fn) => {
  const storage = memoryStorage("viejo");
  const api = createApiClient(mockFetch(401, { error: "Token expirado" }), storage);
  await expect(api[fn](1, {})).rejects.toMatchObject({ status: 401 });
  expect(api.isAuthenticated()).toBe(false);
});

test.each(["/api", "/v1", "http://localhost:5000/api", "https://mi-servidor.com/api", ""])(
  "respeta la URL base %s", async (base) => {
    const fetch = mockFetch(200, { users: [] });
    await createApiClient(fetch, memoryStorage(), base).listUsers();
    expect(fetch.mock.calls[0][0]).toBe((base || "/api") + "/users");
  }
);
