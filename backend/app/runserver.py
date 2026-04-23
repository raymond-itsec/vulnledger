"""Entrypoint used by the container CMD.

Importing ``app.main`` runs :func:`configure_logging` at module load, so
Uvicorn inherits our JSON logging instead of its own defaults.
``log_config=None`` tells Uvicorn to leave logging alone.
"""
import uvicorn

import app.main  # noqa: F401 -- import runs configure_logging()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,
    )
