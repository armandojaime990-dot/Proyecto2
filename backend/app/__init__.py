"""Fabrica de la aplicacion Flask."""
import logging
import os
import time

from flask import Flask, g, jsonify, request
from opentelemetry import metrics, trace
from werkzeug.exceptions import HTTPException

from . import db
from .telemetry import init_telemetry

log = logging.getLogger("app.http")


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///users.db"),
        JWT_SECRET=os.getenv("JWT_SECRET", "cambia-este-secreto-por-uno-largo-de-32-caracteres"),
        JWT_EXPIRES_MIN=int(os.getenv("JWT_EXPIRES_MIN", "120")),
        ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", "admin@demo.com"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "Admin123!"),
        APP_VERSION=os.getenv("APP_VERSION", "dev"),
    )
    if config:
        app.config.update(config)

    init_telemetry(app)  # debe ir antes de abrir conexiones a la BD
    _register_metrics(app)

    from .auth import bp as auth_bp
    from .users import bp as users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.teardown_appcontext(db.close_conn)

    @app.get("/api/health")
    def health():
        db.query("SELECT 1 AS ok", one=True)
        return jsonify(status="ok", version=app.config["APP_VERSION"]), 200

    @app.errorhandler(Exception)
    def handle_error(exc):
        if isinstance(exc, HTTPException):
            return jsonify(error=exc.description), exc.code
        span = trace.get_current_span()
        span.record_exception(exc)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
        log.exception(
            "Excepcion no controlada",
            extra={"event": "unhandled_exception", "http_route": _route(), "error_type": type(exc).__name__},
        )
        return jsonify(error="Error interno del servidor"), 500

    db.init_db(app)
    return app


def _route() -> str:
    rule = request.url_rule
    return rule.rule if rule is not None else "unmatched"


def _register_metrics(app: Flask):
    """Metricas por endpoint: volumen, latencia y errores HTTP (con statusCode)."""
    meter = metrics.get_meter("users-backend")
    requests_counter = meter.create_counter(
        "app_http_requests", unit="1", description="Peticiones HTTP por endpoint y statusCode"
    )
    errors_counter = meter.create_counter(
        "app_http_errors", unit="1", description="Respuestas HTTP con statusCode >= 400"
    )
    latency = meter.create_histogram(
        "app_http_request_duration_ms", unit="ms", description="Latencia de respuesta por endpoint"
    )

    @app.before_request
    def _start_timer():
        g._t0 = time.perf_counter()

    @app.after_request
    def _record(response):
        elapsed_ms = (time.perf_counter() - g.get("_t0", time.perf_counter())) * 1000
        attrs = {
            "http_route": _route(),
            "http_method": request.method,
            "status_code": response.status_code,
        }
        requests_counter.add(1, attrs)
        latency.record(elapsed_ms, attrs)
        if response.status_code >= 400:
            errors_counter.add(1, attrs)

        level = logging.ERROR if response.status_code >= 500 else (
            logging.WARNING if response.status_code >= 400 else logging.INFO
        )
        log.log(
            level,
            f"{request.method} {request.path} -> {response.status_code}",
            extra={
                "event": "http_request",
                "http_route": attrs["http_route"],
                "http_method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(elapsed_ms, 2),
                "client_ip": request.headers.get("X-Real-IP", request.remote_addr),
            },
        )
        return response
