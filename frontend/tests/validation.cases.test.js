// Casos parametrizados de validacion (test.each)
const V = require("../public/js/validation.js");

const VALID_EMAILS = [
  "ana@test.com", "ANA@TEST.COM", "luis.perez@uni.edu.mx", "a@b.co", "user+tag@gmail.com",
  "nombre_apellido@empresa.org", "x1@dominio.net", "first.last@sub.domain.com", "123@numeros.mx",
  "correo-guion@dominio.io", "  espacios@alrededor.com  ", "mayus@Dominio.Com", "a.b.c@d.e.f",
  "admin@demo.com", "soporte@empresa.com.mx", "test@localhost.dev", "q@w.ee", "dev.ops@cloud.aws",
  "nandu@correo.mx", "u_s_e_r@x.y", "mail@mail.mail", "o'brien@irlanda.ie", "a1@b2.c3",
  "longlonglonglong@x.com", "user@123.123.123.com",
];

const INVALID_EMAILS = [
  "", "   ", "ana", "ana@", "@test.com", "ana@test", "ana test@x.com", "ana@te st.com", "ana@@test.com",
  "ana.test.com", "ana@.", "a@b", "sin-arroba", "@", "@@", "ana@test.", ".@", "ana@test@x.com",
  "ana@ test.com", "ana @test.com", "correo@dominio", "user@com", "x@y", null, undefined,
];

test.each(VALID_EMAILS)("email valido: %s", (email) => {
  expect(V.isValidEmail(email)).toBe(true);
});

test.each(INVALID_EMAILS)("email invalido: %s", (email) => {
  expect(V.isValidEmail(email)).toBe(false);
});

const LOGIN_CASES = [
  [{ email: "a@b.com", password: "x" }, []],
  [{ email: "admin@demo.com", password: "Admin123!" }, []],
  [{ email: "  a@b.com  ", password: "1" }, []],
  [{ email: "", password: "x" }, ["email"]],
  [{ email: "   ", password: "x" }, ["email"]],
  [{ email: "malo", password: "x" }, ["email"]],
  [{ email: "a@b", password: "x" }, ["email"]],
  [{ email: "a@b.com", password: "" }, ["password"]],
  [{ email: "a@b.com" }, ["password"]],
  [{ password: "x" }, ["email"]],
  [{}, ["email", "password"]],
  [{ email: "", password: "" }, ["email", "password"]],
  [{ email: "malo", password: "" }, ["email", "password"]],
  [{ email: "@x.com", password: "y" }, ["email"]],
  [{ email: "x@.", password: "y" }, ["email"]],
];

test.each(LOGIN_CASES)("login %j -> errores %j", (data, fields) => {
  expect(Object.keys(V.validateLoginForm(data)).sort()).toEqual(fields.slice().sort());
});

const OK = { name: "Ana", email: "ana@test.com", password: "secreto1", role: "user" };

const CREATE_CASES = [
  [OK, []],
  [{ ...OK, role: "admin" }, []],
  [{ ...OK, name: "Al" }, []],
  [{ ...OK, name: "  Luis  " }, []],
  [{ ...OK, password: "123456" }, []],
  [{ ...OK, password: "x".repeat(64) }, []],
  [{ ...OK, name: "José Pérez" }, []],
  [{ ...OK, email: "ANA@TEST.COM" }, []],
  [{ ...OK, name: "" }, ["name"]],
  [{ ...OK, name: "A" }, ["name"]],
  [{ ...OK, name: "   " }, ["name"]],
  [{ ...OK, name: undefined }, ["name"]],
  [{ ...OK, email: "" }, ["email"]],
  [{ ...OK, email: "malo" }, ["email"]],
  [{ ...OK, email: undefined }, ["email"]],
  [{ ...OK, password: "" }, ["password"]],
  [{ ...OK, password: "12345" }, ["password"]],
  [{ ...OK, password: undefined }, ["password"]],
  [{ ...OK, role: "root" }, ["role"]],
  [{ ...OK, role: "Admin" }, ["role"]],
  [{ ...OK, role: "" }, ["role"]],
  [{ ...OK, role: undefined }, ["role"]],
  [{ name: "A", email: "x", password: "1", role: "x" }, ["email", "name", "password", "role"]],
  [{}, ["email", "name", "password", "role"]],
  [{ ...OK, name: "B", password: "1" }, ["name", "password"]],
];

test.each(CREATE_CASES)("crear %j -> errores %j", (data, fields) => {
  expect(Object.keys(V.validateUserForm(data, false)).sort()).toEqual(fields.slice().sort());
});

const EDIT_CASES = [
  [{ ...OK, password: "" }, []],
  [{ ...OK, password: undefined }, []],
  [{ ...OK, password: "nuevo1" }, []],
  [{ ...OK, role: "admin", password: "" }, []],
  [{ ...OK, name: "Al", password: "" }, []],
  [{ ...OK, password: "1" }, ["password"]],
  [{ ...OK, password: "12345" }, ["password"]],
  [{ ...OK, name: "", password: "" }, ["name"]],
  [{ ...OK, email: "malo", password: "" }, ["email"]],
  [{ ...OK, role: "root", password: "" }, ["role"]],
  [{ ...OK, name: "A", email: "x", password: "" }, ["email", "name"]],
  [{ ...OK, name: "A", password: "1" }, ["name", "password"]],
  [{ name: "", email: "", password: "", role: "" }, ["email", "name", "role"]],
  [{ ...OK, email: "a@b", password: "123" }, ["email", "password"]],
];

test.each(EDIT_CASES)("editar %j -> errores %j", (data, fields) => {
  expect(Object.keys(V.validateUserForm(data, true)).sort()).toEqual(fields.slice().sort());
});
