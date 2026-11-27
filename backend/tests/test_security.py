"""Seguridad de la API: tokens, metodos HTTP y rutas inexistentes."""
import datetime as dt

import jwt
import pytest

from conftest import ADMIN

SECRET = "test-secret-de-pruebas-con-32-bytes-o-mas"

PROTECTED = [
    ("GET", "/api/users"),
    ("GET", "/api/users/1"),
    ("POST", "/api/users"),
    ("PUT", "/api/users/1"),
    ("DELETE", "/api/users/1"),
    ("GET", "/api/auth/me"),
]


def _token(sub="1", secret=SECRET, minutes=60):
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {"sub": sub, "email": "x@x.com", "role": "admin", "iat": now, "exp": now + dt.timedelta(minutes=minutes)},
        secret,
        algorithm="HS256",
    )


BAD_HEADERS = {
    "sin_token": {},
    "esquema_basic": {"Authorization": "Basic YWRtaW46YWRtaW4="},
    "token_malformado": {"Authorization": "Bearer esto-no-es-un-jwt"},
    "firma_incorrecta": {"Authorization": f"Bearer {_token(secret='otro-secreto-distinto-de-32-bytes-xx')}"},
    "token_expirado": {"Authorization": f"Bearer {_token(minutes=-5)}"},
    "usuario_inexistente": {"Authorization": f"Bearer {_token(sub='99999')}"},
}


@pytest.mark.parametrize("method,url", PROTECTED, ids=[f"{m} {u}" for m, u in PROTECTED])
@pytest.mark.parametrize("case", list(BAD_HEADERS))
def test_rutas_protegidas_rechazan_tokens_invalidos(client, method, url, case):
    res = client.open(url, method=method, headers=BAD_HEADERS[case], json={})
    assert res.status_code == 401
    assert "error" in res.get_json()


LOGIN_400 = [
    {},
    {"email": ""},
    {"password": ""},
    {"email": "", "password": ""},
    {"email": ADMIN["email"]},
    {"password": ADMIN["password"]},
    {"email": "   ", "password": "x"},
    {"email": None, "password": None},
]


@pytest.mark.parametrize("payload", LOGIN_400)
def test_login_campos_obligatorios_400(client, payload):
    assert client.post("/api/auth/login", json=payload).status_code == 400


LOGIN_401 = [
    {"email": ADMIN["email"], "password": "admin123!"},
    {"email": ADMIN["email"], "password": "Admin123"},
    {"email": ADMIN["email"], "password": " Admin123!"},
    {"email": "otro@test.com", "password": ADMIN["password"]},
]


@pytest.mark.parametrize("payload", LOGIN_401)
def test_login_credenciales_incorrectas_401(client, payload):
    assert client.post("/api/auth/login", json=payload).status_code == 401


def test_login_email_no_distingue_mayusculas(client):
    res = client.post("/api/auth/login", json={"email": ADMIN["email"].upper(), "password": ADMIN["password"]})
    assert res.status_code == 200


def test_login_cuerpo_no_json_400(client):
    res = client.post("/api/auth/login", data="email=a&password=b", content_type="application/x-www-form-urlencoded")
    assert res.status_code == 400


METHOD_NOT_ALLOWED = [
    ("GET", "/api/auth/login"),
    ("PATCH", "/api/users"),
    ("DELETE", "/api/users"),
    ("PUT", "/api/users"),
    ("POST", "/api/users/1"),
    ("PATCH", "/api/users/1"),
    ("POST", "/api/health"),
    ("DELETE", "/api/health"),
]


@pytest.mark.parametrize("method,url", METHOD_NOT_ALLOWED, ids=[f"{m} {u}" for m, u in METHOD_NOT_ALLOWED])
def test_metodo_no_permitido_405(client, method, url):
    assert client.open(url, method=method).status_code == 405


NOT_FOUND = [
    "/api", "/api/", "/api/usuarios", "/api/users/abc", "/api/auth", "/api/auth/logout", 
]


@pytest.mark.parametrize("url", NOT_FOUND)
def test_ruta_inexistente_404(client, auth, url):
    res = client.get(url, headers=auth)
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_token_de_usuario_eliminado_es_rechazado(client, auth):
    uid = client.post(
        "/api/users", json={"name": "Temporal", "email": "tmp@test.com", "password": "secreto1"}, headers=auth
    ).get_json()["user"]["id"]
    token = client.post("/api/auth/login", json={"email": "tmp@test.com", "password": "secreto1"}).get_json()["token"]
    client.delete(f"/api/users/{uid}", headers=auth)
    assert client.get("/api/users", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_respuesta_de_login_no_expone_hash(client):
    body = client.post("/api/auth/login", json=ADMIN).get_data(as_text=True)
    assert "password_hash" not in body
    assert ADMIN["password"] not in body
