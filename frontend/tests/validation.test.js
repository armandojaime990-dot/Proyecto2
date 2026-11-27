const V = require("../public/js/validation.js");

describe("isValidEmail", () => {
  test("acepta emails validos", () => {
    expect(V.isValidEmail("ana@test.com")).toBe(true);
    expect(V.isValidEmail("  luis.p@uni.edu.mx ")).toBe(true);
  });
  test("rechaza emails invalidos", () => {
    expect(V.isValidEmail("ana")).toBe(false);
    expect(V.isValidEmail("ana@test")).toBe(false);
    expect(V.isValidEmail("")).toBe(false);
    expect(V.isValidEmail(null)).toBe(false);
  });
});

describe("validateLoginForm", () => {
  test("sin errores con datos correctos", () => {
    expect(V.validateLoginForm({ email: "a@b.com", password: "x" })).toEqual({});
  });
  test("marca campos vacios", () => {
    const e = V.validateLoginForm({ email: "", password: "" });
    expect(e.email).toBeDefined();
    expect(e.password).toBeDefined();
  });
  test("marca email invalido", () => {
    expect(V.validateLoginForm({ email: "malo", password: "x" }).email).toBe("Email invalido");
  });
});

describe("validateUserForm", () => {
  const ok = { name: "Ana", email: "ana@test.com", password: "secreto1", role: "user" };

  test("usuario valido", () => {
    expect(V.hasErrors(V.validateUserForm(ok, false))).toBe(false);
  });
  test("todos los campos invalidos", () => {
    const e = V.validateUserForm({ name: "A", email: "x", password: "1", role: "jefe" }, false);
    expect(Object.keys(e).sort()).toEqual(["email", "name", "password", "role"]);
  });
  test("al crear la contrasena es obligatoria", () => {
    expect(V.validateUserForm({ ...ok, password: "" }, false).password).toBeDefined();
  });
  test("al editar la contrasena vacia es valida", () => {
    expect(V.validateUserForm({ ...ok, password: "" }, true)).toEqual({});
  });
  test("al editar una contrasena corta no es valida", () => {
    expect(V.validateUserForm({ ...ok, password: "123" }, true).password).toBeDefined();
  });
});
