"""Login con JWT y decorador de proteccion de rutas."""
import datetime as dt
import functools
import logging

import jwt
from flask import Blueprint, current_app, g, jsonify, request
from opentelemetry import trace
from werkzeug.security import check_password_hash

from . import db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
log = logging.getLogger("app.auth")
tracer = trace.get_tracer("app.auth")


def create_token(user: dict) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "iat": now,
        "exp": now + dt.timedelta(minutes=current_app.config["JWT_EXPIRES_MIN"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="Token requerido"), 401
        token = header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify(error="Token expirado"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="Token invalido"), 401
        user = db.query(
            "SELECT id, name, email, role, created_at FROM users WHERE id = ?",
            (int(payload["sub"]),),
            one=True,
        )
        if user is None:
            return jsonify(error="Usuario no existe"), 401
        g.current_user = user
        trace.get_current_span().set_attribute("enduser.id", str(user["id"]))
        return fn(*args, **kwargs)

    return wrapper


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify(error="Email y contrasena son obligatorios"), 400

    user = db.query(
        "SELECT id, name, email, role, password_hash FROM users WHERE email = ?",
        (email,),
        one=True,
    )
    with tracer.start_as_current_span("auth.verify_password"):
        valid = user is not None and check_password_hash(user["password_hash"], password)

    if not valid:
        log.warning("Login fallido", extra={"event": "login_failed", "login_email": email})
        return jsonify(error="Credenciales invalidas"), 401

    log.info("Login exitoso", extra={"event": "login_success", "user_id": user["id"]})
    token = create_token(user)
    user.pop("password_hash")
    return jsonify(token=token, user=user), 200


@bp.get("/me")
@login_required
def me():
    return jsonify(user=_serialize(g.current_user)), 200


def _serialize(user: dict) -> dict:
    out = dict(user)
    if out.get("created_at") is not None and not isinstance(out["created_at"], str):
        out["created_at"] = out["created_at"].isoformat()
    return out
