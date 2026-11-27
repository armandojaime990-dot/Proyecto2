NEW_USER = {"name": "Ana Lopez", "email": "ana@test.com", "password": "secreto1", "role": "user"}


def _create(client, auth, **overrides):
    return client.post("/api/users", json={**NEW_USER, **overrides}, headers=auth)


def test_listar_requiere_login(client):
    assert client.get("/api/users").status_code == 401


def test_listar_incluye_admin(client, auth):
    res = client.get("/api/users", headers=auth)
    assert res.status_code == 200
    assert len(res.get_json()["users"]) == 1


def test_crear_usuario(client, auth):
    res = _create(client, auth)
    assert res.status_code == 201
    user = res.get_json()["user"]
    assert user["id"] > 0
    assert user["email"] == "ana@test.com"
    assert "password_hash" not in user


def test_crear_usuario_puede_hacer_login(client, auth):
    _create(client, auth)
    res = client.post("/api/auth/login", json={"email": "ana@test.com", "password": "secreto1"})
    assert res.status_code == 200


def test_crear_email_duplicado_409(client, auth):
    _create(client, auth)
    assert _create(client, auth).status_code == 409


def test_crear_datos_invalidos_400(client, auth):
    res = _create(client, auth, name="A", email="no-es-email", password="123", role="jefe")
    assert res.status_code == 400
    assert set(res.get_json()["fields"]) == {"name", "email", "password", "role"}


def test_obtener_usuario(client, auth):
    uid = _create(client, auth).get_json()["user"]["id"]
    res = client.get(f"/api/users/{uid}", headers=auth)
    assert res.status_code == 200
    assert res.get_json()["user"]["name"] == "Ana Lopez"


def test_obtener_inexistente_404(client, auth):
    assert client.get("/api/users/9999", headers=auth).status_code == 404


def test_actualizar_usuario(client, auth):
    uid = _create(client, auth).get_json()["user"]["id"]
    res = client.put(f"/api/users/{uid}", json={"name": "Ana Maria", "role": "admin"}, headers=auth)
    assert res.status_code == 200
    assert res.get_json()["user"]["name"] == "Ana Maria"
    assert res.get_json()["user"]["role"] == "admin"


def test_actualizar_password(client, auth):
    uid = _create(client, auth).get_json()["user"]["id"]
    client.put(f"/api/users/{uid}", json={"password": "nuevo123"}, headers=auth)
    res = client.post("/api/auth/login", json={"email": "ana@test.com", "password": "nuevo123"})
    assert res.status_code == 200


def test_actualizar_inexistente_404(client, auth):
    assert client.put("/api/users/9999", json={"name": "Xx"}, headers=auth).status_code == 404


def test_actualizar_email_duplicado_409(client, auth):
    uid = _create(client, auth).get_json()["user"]["id"]
    res = client.put(f"/api/users/{uid}", json={"email": "admin@test.com"}, headers=auth)
    assert res.status_code == 409


def test_eliminar_usuario(client, auth):
    uid = _create(client, auth).get_json()["user"]["id"]
    assert client.delete(f"/api/users/{uid}", headers=auth).status_code == 204
    assert client.get(f"/api/users/{uid}", headers=auth).status_code == 404


def test_eliminar_inexistente_404(client, auth):
    assert client.delete("/api/users/9999", headers=auth).status_code == 404


def test_no_puede_eliminarse_a_si_mismo(client, auth):
    me = client.get("/api/auth/me", headers=auth).get_json()["user"]
    assert client.delete(f"/api/users/{me['id']}", headers=auth).status_code == 400
