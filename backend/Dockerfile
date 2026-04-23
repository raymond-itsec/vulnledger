FROM python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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

CMD ["/bin/sh", "-c", "alembic upgrade head && exec python -m app.runserver"]
