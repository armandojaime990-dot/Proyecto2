"""CRUD de usuarios con multiples casos de datos."""
import pytest

USERS = [
    ("Ana Lopez", "ana@test.com", "user"),
    ("Luis Perez", "luis@test.com", "admin"),
    ("María José", "maria.jose@uni.mx", "user"),
    ("José Ángel", "jose.angel@uni.mx", "admin"),
    ("Pedro Páramo", "pedro@comala.mx", "user"),
    ("Sor Juana", "sor.juana@nueva.es", "admin"),
    ("Frida K", "frida@coyoacan.mx", "user"),
    ("Diego R", "diego@murales.mx", "user"),
    ("Octavio P", "octavio@laberinto.mx", "admin"),
    ("Rosario C", "rosario@balun.mx", "user"),
    ("Jean-Luc", "jl@picard.fr", "user"),
    ("O'Connor", "oconnor@irlanda.ie", "user"),
    ("李小龙", "bruce@lee.cn", "user"),
    ("Usuario 13", "u13+tag@gmail.com", "admin"),
    ("Nombre Muy Largo De Prueba Para Validar", "largo@test.com", "user"),
    ("Al", "al@x.co", "user"),
    ("Zoe", "zoe@x.io", "admin"),
    ("Ñoño", "nono@test.mx", "user"),
    ("<b>html</b>", "html@test.com", "user"),
    ("Robert'); DROP TABLE users;--", "bobby@tables.com", "user"),
]


def _create(client, auth, name, email, role, password="secreto1"):
    return client.post("/api/users", json={"name": name, "email": email, "password": password, "role": role}, headers=auth)


@pytest.mark.parametrize("name,email,role", USERS)
def test_crear_y_consultar(client, auth, name, email, role):
    res = _create(client, auth, name, email, role)
    assert res.status_code == 201
    user = res.get_json()["user"]
    got = client.get(f"/api/users/{user['id']}", headers=auth).get_json()["user"]
    assert (got["name"], got["email"], got["role"]) == (name, email, role)


@pytest.mark.parametrize("name,email,role", USERS[:5])
def test_usuario_creado_puede_iniciar_sesion(client, auth, name, email, role):
    _create(client, auth, name, email, role, password=f"pwd-{email}")
    res = client.post("/api/auth/login", json={"email": email, "password": f"pwd-{email}"})
    assert res.status_code == 200
    assert res.get_json()["user"]["role"] == role


NEW_NAMES = ["Ana María", "Bo", "Carlos III", "Dña. Elena", "Éric", "Fátima", "Gö", "Hugo 2", "Iñaki", "Juan-Pablo"]


@pytest.mark.parametrize("new_name", NEW_NAMES)
def test_actualizar_nombre(client, auth, new_name):
    uid = _create(client, auth, "Original", "orig@test.com", "user").get_json()["user"]["id"]
    res = client.put(f"/api/users/{uid}", json={"name": new_name}, headers=auth)
    assert res.status_code == 200
    assert res.get_json()["user"]["name"] == new_name
    assert res.get_json()["user"]["email"] == "orig@test.com"


@pytest.mark.parametrize("start,end", [("user", "admin"), ("admin", "user")])
def test_cambiar_rol(client, auth, start, end):
    uid = _create(client, auth, "Rol", "rol@test.com", start).get_json()["user"]["id"]
    assert client.put(f"/api/users/{uid}", json={"role": end}, headers=auth).get_json()["user"]["role"] == end


@pytest.mark.parametrize("new_email", ["nuevo@test.com", "NUEVO2@TEST.COM", "x.y@z.mx", "a+b@c.io", "otro@dominio.org"])
def test_actualizar_email(client, auth, new_email):
    uid = _create(client, auth, "Correo", "correo@test.com", "user").get_json()["user"]["id"]
    res = client.put(f"/api/users/{uid}", json={"email": new_email}, headers=auth)
    assert res.status_code == 200
    assert res.get_json()["user"]["email"] == new_email.lower()


MISSING_IDS = [2, 3, 50, 999, 12345, 2147483647, 7, 100]


@pytest.mark.parametrize("uid", MISSING_IDS)
def test_get_inexistente_404(client, auth, uid):
    assert client.get(f"/api/users/{uid}", headers=auth).status_code == 404


@pytest.mark.parametrize("uid", MISSING_IDS)
def test_put_inexistente_404(client, auth, uid):
    assert client.put(f"/api/users/{uid}", json={"name": "Nadie"}, headers=auth).status_code == 404


@pytest.mark.parametrize("uid", MISSING_IDS)
def test_delete_inexistente_404(client, auth, uid):
    assert client.delete(f"/api/users/{uid}", headers=auth).status_code == 404


DUP_VARIANTS = [
    "dup@test.com", "DUP@test.com", "Dup@Test.Com", "DUP@TEST.COM", " dup@test.com", "dup@test.com ",
    ]


@pytest.mark.parametrize("variant", DUP_VARIANTS)
def test_email_duplicado_sin_importar_mayusculas_409(client, auth, variant):
    assert _create(client, auth, "Primero", "dup@test.com", "user").status_code == 201
    res = _create(client, auth, "Segundo", variant, "user")
    assert res.status_code == 409


INVALID_CREATE = [
    ({"email": "a@b.com", "password": "secreto1"}, {"name"}),
    ({"name": "Ana", "password": "secreto1"}, {"email"}),
    ({"name": "Ana", "email": "a@b.com"}, {"password"}),
    ({"name": "Ana", "email": "a@b.com", "password": "secreto1", "role": "root"}, {"role"}),
    ({"name": "A", "email": "a@b.com", "password": "secreto1"}, {"name"}),
    ({"name": "Ana", "email": "malo", "password": "secreto1"}, {"email"}),
    ({"name": "Ana", "email": "a@b.com", "password": "123"}, {"password"}),
    ({"name": "", "email": "", "password": ""}, {"name", "email", "password"}),
    ({}, {"name", "email", "password"}),
    ({"name": "A", "email": "x", "password": "1", "role": "x"}, {"name", "email", "password", "role"}),
    ({"name": "Ana", "email": "a@b", "password": "12345"}, {"email", "password"}),
    ({"name": " ", "email": "a@b.com", "password": "secreto1"}, {"name"}),
    ({"name": "Ana", "email": "a b@c.com", "password": "secreto1"}, {"email"}),
    ({"name": "Ana", "email": "a@b.com", "password": "secreto1", "role": "ADMIN"}, {"role"}),
    ({"name": None, "email": None, "password": None}, {"name", "email", "password"}),
]


@pytest.mark.parametrize("payload,fields", INVALID_CREATE)
def test_crear_invalido_indica_campos(client, auth, payload, fields):
    res = client.post("/api/users", json=payload, headers=auth)
    assert res.status_code == 400
    assert set(res.get_json()["fields"]) == fields


INVALID_UPDATE = [
    {"name": "A"}, {"email": "malo"}, {"password": "123"}, {"role": "root"}, {"name": ""}, {"email": ""},
]


@pytest.mark.parametrize("payload", INVALID_UPDATE)
def test_actualizar_invalido_400(client, auth, payload):
    uid = _create(client, auth, "Valido", "valido@test.com", "user").get_json()["user"]["id"]
    assert client.put(f"/api/users/{uid}", json=payload, headers=auth).status_code == 400


def test_actualizar_sin_campos_400(client, auth):
    uid = _create(client, auth, "Valido", "valido@test.com", "user").get_json()["user"]["id"]
    assert client.put(f"/api/users/{uid}", json={}, headers=auth).status_code == 400


@pytest.mark.parametrize("n", range(1, 6))
def test_eliminar_quita_de_la_lista(client, auth, n):
    ids = [_create(client, auth, f"Borrar {i}", f"b{i}@test.com", "user").get_json()["user"]["id"] for i in range(n)]
    victim = ids[-1]
    assert client.delete(f"/api/users/{victim}", headers=auth).status_code == 204
    remaining = [u["id"] for u in client.get("/api/users", headers=auth).get_json()["users"]]
    assert victim not in remaining
    assert len(remaining) == n


def test_eliminar_dos_veces_404(client, auth):
    uid = _create(client, auth, "Doble", "doble@test.com", "user").get_json()["user"]["id"]
    assert client.delete(f"/api/users/{uid}", headers=auth).status_code == 204
    assert client.delete(f"/api/users/{uid}", headers=auth).status_code == 404
