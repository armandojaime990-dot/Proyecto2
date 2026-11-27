"""CRUD de usuarios (todas las rutas requieren login)."""
import logging
import re

from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash

from . import db
from .auth import _serialize, login_required

bp = Blueprint("users", __name__, url_prefix="/api/users")
log = logging.getLogger("app.users")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLES = ("admin", "user")
PUBLIC_COLS = "id, name, email, role, created_at"


def validate_user(data: dict, partial: bool = False):
    """Devuelve (datos_limpios, errores)."""
    errors = {}
    clean = {}

    if "name" in data or not partial:
        name = (data.get("name") or "").strip()
        if len(name) < 2:
            errors["name"] = "El nombre debe tener al menos 2 caracteres"
        clean["name"] = name

    if "email" in data or not partial:
        email = (data.get("email") or "").strip().lower()
        if not EMAIL_RE.match(email):
            errors["email"] = "Email invalido"
        clean["email"] = email

    if "password" in data or not partial:
        password = data.get("password") or ""
        if partial and password == "":
            pass  # en edicion, contrasena vacia = no cambiarla
        elif len(password) < 6:
            errors["password"] = "La contrasena debe tener al menos 6 caracteres"
        else:
            clean["password"] = password

    if "role" in data or not partial:
        role = data.get("role") or "user"
        if role not in ROLES:
            errors["role"] = "Rol invalido (admin o user)"
        clean["role"] = role

    return clean, errors


def ensure_admin(name: str, email: str, password: str):
    exists = db.query("SELECT id FROM users WHERE email = ?", (email.lower(),), one=True)
    if exists:
        return
    db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email.lower(), generate_password_hash(password), "admin"),
    )
    log.info("Usuario administrador inicial creado", extra={"event": "admin_seeded"})


@bp.get("")
@login_required
def list_users():
    rows = db.query(f"SELECT {PUBLIC_COLS} FROM users ORDER BY id")
    return jsonify(users=[_serialize(r) for r in rows]), 200


@bp.get("/<int:user_id>")
@login_required
def get_user(user_id: int):
    row = db.query(f"SELECT {PUBLIC_COLS} FROM users WHERE id = ?", (user_id,), one=True)
    if row is None:
        return jsonify(error="Usuario no encontrado"), 404
    return jsonify(user=_serialize(row)), 200


@bp.post("")
@login_required
def create_user():
    data = request.get_json(silent=True) or {}
    clean, errors = validate_user(data)
    if errors:
        return jsonify(error="Datos invalidos", fields=errors), 400
    try:
        row = db.execute(
            f"INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?) "
            f"RETURNING {PUBLIC_COLS}",
            (clean["name"], clean["email"], generate_password_hash(clean["password"]), clean["role"]),
            returning=True,
        )
    except db.IntegrityError:
        return jsonify(error="El email ya esta registrado", fields={"email": "Duplicado"}), 409
    log.info(
        "Usuario creado",
        extra={"event": "user_created", "user_id": row["id"], "by_user": g.current_user["id"]},
    )
    return jsonify(user=_serialize(row)), 201


@bp.put("/<int:user_id>")
@login_required
def update_user(user_id: int):
    if db.query("SELECT id FROM users WHERE id = ?", (user_id,), one=True) is None:
        return jsonify(error="Usuario no encontrado"), 404
    data = request.get_json(silent=True) or {}
    clean, errors = validate_user(data, partial=True)
    if errors:
        return jsonify(error="Datos invalidos", fields=errors), 400
    if not clean:
        return jsonify(error="No hay campos para actualizar"), 400

    sets, params = [], []
    for field in ("name", "email", "role"):
        if field in clean:
            sets.append(f"{field} = ?")
            params.append(clean[field])
    if "password" in clean:
        sets.append("password_hash = ?")
        params.append(generate_password_hash(clean["password"]))
    params.append(user_id)
    try:
        row = db.execute(
            f"UPDATE users SET {', '.join(sets)} WHERE id = ? RETURNING {PUBLIC_COLS}",
            tuple(params),
            returning=True,
        )
    except db.IntegrityError:
        return jsonify(error="El email ya esta registrado", fields={"email": "Duplicado"}), 409
    log.info(
        "Usuario actualizado",
        extra={"event": "user_updated", "user_id": user_id, "by_user": g.current_user["id"]},
    )
    return jsonify(user=_serialize(row)), 200


@bp.delete("/<int:user_id>")
@login_required
def delete_user(user_id: int):
    if user_id == g.current_user["id"]:
        return jsonify(error="No puedes eliminar tu propio usuario"), 400
    count = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if count == 0:
        return jsonify(error="Usuario no encontrado"), 404
    log.info(
        "Usuario eliminado",
        extra={"event": "user_deleted", "user_id": user_id, "by_user": g.current_user["id"]},
    )
    return "", 204
