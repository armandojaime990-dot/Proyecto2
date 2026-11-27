import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402

ADMIN = {"email": "admin@test.com", "password": "Admin123!"}


@pytest.fixture()
def app(tmp_path):
    os.environ["OTEL_ENABLED"] = "false"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
            "JWT_SECRET": "test-secret-de-pruebas-con-32-bytes-o-mas",
            "ADMIN_EMAIL": ADMIN["email"],
            "ADMIN_PASSWORD": ADMIN["password"],
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def token(client):
    res = client.post("/api/auth/login", json=ADMIN)
    assert res.status_code == 200
    return res.get_json()["token"]


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}
