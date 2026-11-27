"""Pruebas unitarias de las reglas de validacion de usuarios (validate_user)."""
import pytest

from app.users import validate_user

BASE = {"name": "Ana Lopez", "email": "ana@test.com", "password": "secreto1", "role": "user"}

VALID_EMAILS = [
    "ana@test.com", "ANA@TEST.COM", "luis.perez@uni.edu.mx", "a@b.co", "user+tag@gmail.com",
    "nombre_apellido@empresa.org", "x1@dominio.net", "first.last@sub.domain.com", "123@numeros.mx",
    "correo-guion@dominio.io", "  espacios@alrededor.com  ", "mayus@Dominio.Com", "a.b.c@d.e.f",
    "test@localhost.dev", "q@w.ee", "dev.ops@cloud.aws",
    "user@123.123.123.com", "u_s_e_r@x.y", "long" * 10 + "@x.com",
    ]

INVALID_EMAILS = [
    "", "   ", "ana", "ana@", "@test.com", "ana@test", "ana test@x.com", "ana@te st.com", "ana@@test.com",
    "ana.test.com", "ana@.", "a@b", "sin-arroba", "@", "@@", "ana@test.", ".@", "ana@test@x.com",
    "ana@ test.com", "ana @test.com", "\t@\t.\t", "correo@dominio", "user@com", "x@y", None,
]

VALID_NAMES = [
    "Al", "Ana", "Ana Lopez", "José Pérez", "María de los Ángeles", "O'Connor", "Jean-Luc",
    "李小龙", "Ñoño", "A" * 120, "  Luis  ", "Dr. Ramírez", "Usuario 123", "ab", "Zoe",
]

INVALID_NAMES = ["", " ", "A", "  B  ", None, "\t", "\n", "   x   ", "Z", "   "]

VALID_PASSWORDS = [
    "123456", "secreto1", "Admin123!", "abcdef", "      ", "contraseña", "P@ssw0rd", "x" * 6,
    "x" * 64, "ñañañá", "12345678901234567890", "!@#$%^",
]

INVALID_PASSWORDS = ["", "1", "12", "123", "1234", "12345", "abc", "xyz12", None, " ", "aaaaa", "!@#$"]

VALID_ROLES = ["admin", "user"]

INVALID_ROLES = ["Admin", "USER", "root", "superadmin", "jefe", "guest", "administrador", "usuario", "1", "admin "]


@pytest.mark.parametrize("email", VALID_EMAILS)
def test_email_valido(email):
    clean, errors = validate_user({**BASE, "email": email})
    assert "email" not in errors
    assert clean["email"] == email.strip().lower()


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_email_invalido(email):
    _, errors = validate_user({**BASE, "email": email})
    assert errors["email"] == "Email invalido"


@pytest.mark.parametrize("name", VALID_NAMES)
def test_nombre_valido(name):
    clean, errors = validate_user({**BASE, "name": name})
    assert "name" not in errors
    assert clean["name"] == name.strip()


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_nombre_invalido(name):
    _, errors = validate_user({**BASE, "name": name})
    assert "name" in errors


@pytest.mark.parametrize("password", VALID_PASSWORDS)
def test_password_valido(password):
    clean, errors = validate_user({**BASE, "password": password})
    assert "password" not in errors
    assert clean["password"] == password


@pytest.mark.parametrize("password", INVALID_PASSWORDS)
def test_password_invalido(password):
    _, errors = validate_user({**BASE, "password": password})
    assert "password" in errors


@pytest.mark.parametrize("role", VALID_ROLES)
def test_rol_valido(role):
    clean, errors = validate_user({**BASE, "role": role})
    assert errors == {}
    assert clean["role"] == role


@pytest.mark.parametrize("role", INVALID_ROLES)
def test_rol_invalido(role):
    _, errors = validate_user({**BASE, "role": role})
    assert "role" in errors


def test_rol_por_defecto_es_user():
    data = {k: v for k, v in BASE.items() if k != "role"}
    clean, errors = validate_user(data)
    assert errors == {}
    assert clean["role"] == "user"


def test_edicion_parcial_sin_campos_no_tiene_errores():
    assert validate_user({}, partial=True) == ({}, {})


def test_edicion_parcial_password_vacio_se_ignora():
    clean, errors = validate_user({"password": ""}, partial=True)
    assert errors == {}
    assert "password" not in clean


def test_edicion_parcial_password_corto_es_error():
    _, errors = validate_user({"password": "123"}, partial=True)
    assert "password" in errors


def test_creacion_vacia_marca_campos_obligatorios():
    _, errors = validate_user({})
    assert set(errors) == {"name", "email", "password"}
