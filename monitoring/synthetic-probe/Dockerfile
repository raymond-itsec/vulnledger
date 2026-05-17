FROM python:3.14.5-slim-bookworm@sha256:a3974109d36f164ca70024bc0d0828ac706e4ccda849f8638d879e91f79e90ec

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY probe.py ./

RUN useradd --create-home --shell /usr/sbin/nologin probe
USER probe

EXPOSE 8900

CMD ["python", "probe.py"]
