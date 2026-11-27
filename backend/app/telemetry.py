"""Instrumentacion OpenTelemetry (OTLP/HTTP) hacia OpenObserve: trazas, metricas y logs.

Se activa con OTEL_ENABLED=true. En pruebas queda apagada y el codigo usa la API
de OpenTelemetry en modo no-op, por lo que la aplicacion funciona igual.
"""
import base64
import json
import logging
import os
import sys


class JsonFormatter(logging.Formatter):
    """Logs estructurados (JSON) para la salida estandar del contenedor."""

    RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}

    def format(self, record):
        data = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self.RESERVED and not key.startswith("_"):
                data[key] = value
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str, ensure_ascii=False)


def setup_stdout_logging():
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    if not any(getattr(h, "_app_stdout", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._app_stdout = True
        root.addHandler(handler)


def _auth_headers():
    user = os.getenv("O2_USER", "")
    password = os.getenv("O2_PASSWORD", "")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def init_telemetry(app):
    setup_stdout_logging()
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        app.logger.info("OpenTelemetry deshabilitado (OTEL_ENABLED != true)")
        return False

    # Importes aqui: solo se necesitan en produccion (ver requirements.txt)
    from opentelemetry import metrics, trace
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Ej.: http://openobserve:5080/api/default  (sin "/" final)
    base = os.getenv("O2_OTLP_ENDPOINT", "http://openobserve:5080/api/default").rstrip("/")
    headers = _auth_headers()
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "users-backend"),
            "service.version": os.getenv("APP_VERSION", "dev"),
            "deployment.environment": os.getenv("APP_ENV", "production"),
        }
    )

    # Trazas
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces", headers=headers))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metricas (se exportan cada 10 s)
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics", headers=headers),
        export_interval_millis=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "10000")),
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    # Logs
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{base}/v1/logs", headers=headers))
    )
    set_logger_provider(logger_provider)
    logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    # Auto-instrumentacion: peticiones HTTP (Flask) y consultas SQL (PostgreSQL)
    FlaskInstrumentor().instrument_app(app)
    Psycopg2Instrumentor().instrument(skip_dep_check=True)

    app.logger.info("OpenTelemetry habilitado", extra={"event": "otel_enabled", "otlp_base": base})
    return True
