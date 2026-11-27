from conftest import ADMIN


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_login_ok_devuelve_token_y_usuario(client):
    res = client.post("/api/auth/login", json=ADMIN)
    body = res.get_json()
    assert res.status_code == 200
    assert body["token"]
    assert body["user"]["email"] == ADMIN["email"]
    assert "password_hash" not in body["user"]


def test_login_password_incorrecto(client):
    res = client.post("/api/auth/login", json={"email": ADMIN["email"], "password": "malo"})
    assert res.status_code == 401


def test_login_usuario_inexistente(client):
    res = client.post("/api/auth/login", json={"email": "nadie@test.com", "password": "x123456"})
    assert res.status_code == 401


def test_login_campos_vacios(client):
    res = client.post("/api/auth/login", json={})
    assert res.status_code == 400


def test_me_con_token(client, auth):
    res = client.get("/api/auth/me", headers=auth)
    assert res.status_code == 200
    assert res.get_json()["user"]["role"] == "admin"


def test_me_sin_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_token_invalido(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert res.status_code == 401


def test_ruta_inexistente_404(client):
    assert client.get("/api/no-existe").status_code == 404
