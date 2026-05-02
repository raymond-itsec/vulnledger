"""Process-wide logging configuration.

Emits one JSON object per log line to stdout so container runtimes and
downstream aggregators can parse without regex. Uvicorn access/error loggers
propagate to the root handler so they share the same format.

A `RequestIDFilter` injects per-request correlation IDs into every log
record (see `app.middleware.request_id`). When emitted from outside an
HTTP request (startup, shutdown, background tasks), both ID fields are
absent from the record entirely - the JSON output omits them rather than
including misleading nulls.
"""
import logging
import logging.config

from app.config import settings
from app.middleware.request_id import vl_request_id_var, x_request_id_var


class RequestIDFilter(logging.Filter):
    """Pull `x_request_id` and `vl_request_id` from contextvars onto the
    record. Always sets both attributes, even when their contextvar is
    None (e.g., log lines emitted outside an HTTP request lifecycle).
    `pythonjsonlogger` renders `None` as JSON `null`, so log consumers
    can distinguish "no value" from a real value unambiguously.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.x_request_id = x_request_id_var.get()
        record.vl_request_id = vl_request_id_var.get()
        return True


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": RequestIDFilter,
                },
            },
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    # The format string declares *which* fields the
                    # formatter is willing to emit; missing attributes on
                    # a record are silently omitted from the output, so
                    # it is safe to declare x_request_id / vl_request_id
                    # here even though many records won't carry them.
                    "format": (
                        "%(asctime)s %(levelname)s %(name)s "
                        "%(x_request_id)s %(vl_request_id)s %(message)s"
                    ),
                    "rename_fields": {
                        "asctime": "ts",
                        "levelname": "level",
                        "name": "logger",
                    },
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "json",
                    "filters": ["request_id"],
                },
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["stdout"],
            },
            "loggers": {
                "uvicorn": {"level": settings.log_level, "handlers": [], "propagate": True},
                "uvicorn.error": {"level": settings.log_level, "handlers": [], "propagate": True},
                "uvicorn.access": {"level": settings.log_level, "handlers": [], "propagate": True},
            },
        }
    )
