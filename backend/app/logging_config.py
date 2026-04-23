"""Process-wide logging configuration.

Emits one JSON object per log line to stdout so container runtimes and
downstream aggregators can parse without regex. Uvicorn access/error loggers
propagate to the root handler so they share the same format.
"""
import logging.config

from app.config import settings


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
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
