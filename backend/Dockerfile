FROM python:3.14.5-slim-bookworm@sha256:a3974109d36f164ca70024bc0d0828ac706e4ccda849f8638d879e91f79e90ec

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY app/ app/
COPY templates/ templates/
COPY alembic/ alembic/
COPY alembic.ini .

RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app

EXPOSE 8000

USER appuser

# Mint a single per-container-restart BOOT_ID up-front and export it
# so both the alembic migration process AND the uvicorn process inherit
# the same correlation ID. Without this, the two child Pythons would
# each mint their own (request_id.py imports independently per
# process), producing two BOOT-<uuid> values per restart and making
# "everything from this restart" hard to grep.
# /proc/sys/kernel/random/uuid is the kernel-supplied UUID source; it
# avoids the uuidgen binary which is not in slim images.
CMD ["/bin/sh", "-c", "export BOOT_ID=\"BOOT-$(cat /proc/sys/kernel/random/uuid)\" && alembic upgrade head && exec python -m app.runserver"]
