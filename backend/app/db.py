"""Capa de acceso a datos.

Soporta PostgreSQL (produccion, via psycopg2) y SQLite (pruebas con pytest).
Las consultas se escriben con '?' y se traducen a '%s' cuando el motor es PostgreSQL.
"""
import logging
import os
import sqlite3
import time

from flask import current_app, g

log = logging.getLogger("app.db")

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


class IntegrityError(Exception):
    """Violacion de restriccion (por ejemplo, email duplicado)."""


def _is_pg(url: str) -> bool:
    return url.startswith("postgres")


def _connect(url: str):
    if _is_pg(url):
        import psycopg2  # importado aqui para que las pruebas no lo necesiten

        return psycopg2.connect(url)
    path = url.replace("sqlite:///", "", 1)
    conn = sqlite3.connect(path, check_same_thread=False)
    return conn


def get_conn():
    if "db_conn" not in g:
        g.db_conn = _connect(current_app.config["DATABASE_URL"])
    return g.db_conn


def close_conn(_exc=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


def _translate(sql: str) -> str:
    if _is_pg(current_app.config["DATABASE_URL"]):
        return sql.replace("?", "%s")
    return sql


def _rows_to_dicts(cur):
    if cur.description is None:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def query(sql: str, params=(), one=False):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(_translate(sql), params)
        rows = _rows_to_dicts(cur)
    finally:
        cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql: str, params=(), returning=False):
    """Ejecuta INSERT/UPDATE/DELETE. Devuelve la fila de RETURNING o el rowcount."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(_translate(sql), params)
        result = _rows_to_dicts(cur) if returning else cur.rowcount
        conn.commit()
        return result[0] if returning and result else result
    except Exception as exc:  # traducimos errores de integridad de ambos motores
        conn.rollback()
        if exc.__class__.__name__ in ("IntegrityError", "UniqueViolation"):
            raise IntegrityError(str(exc)) from exc
        raise
    finally:
        cur.close()


def init_db(app, retries: int = 30):
    """Crea la tabla y el usuario administrador inicial (reintenta mientras la BD arranca)."""
    url = app.config["DATABASE_URL"]
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            conn = _connect(url)
            break
        except Exception as exc:  # pragma: no cover - solo pasa con Postgres arrancando
            last_exc = exc
            log.warning("BD no disponible (intento %s/%s): %s", attempt, retries, exc)
            time.sleep(2)
    else:  # pragma: no cover
        raise RuntimeError(f"No se pudo conectar a la base de datos: {last_exc}")

    cur = conn.cursor()
    cur.execute(SCHEMA_PG if _is_pg(url) else SCHEMA_SQLITE)
    conn.commit()
    cur.close()
    conn.close()

    with app.app_context():
        from .users import ensure_admin

        ensure_admin(
            os.getenv("ADMIN_NAME", "Administrador"),
            app.config["ADMIN_EMAIL"],
            app.config["ADMIN_PASSWORD"],
        )
