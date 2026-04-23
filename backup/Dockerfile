FROM postgres:16.13-alpine3.23

# Supercronic: cron for containers that runs as non-root.
ARG TARGETARCH
ARG SUPERCRONIC_VERSION=0.2.44
ARG SUPERCRONIC_SHA1_AMD64=6eb0a8e1e6673675dc67668c1a9b6409f79c37bc
ARG SUPERCRONIC_SHA1_ARM64=6c6cba4cde1dd4a1dd1e7fb23498cde1b57c226c

RUN set -eux; \
    apk add --no-cache --virtual .fetch-deps ca-certificates wget; \
    case "${TARGETARCH:-amd64}" in \
      amd64) arch=amd64; sha1="${SUPERCRONIC_SHA1_AMD64}" ;; \
      arm64) arch=arm64; sha1="${SUPERCRONIC_SHA1_ARM64}" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    url="https://github.com/aptible/supercronic/releases/download/v${SUPERCRONIC_VERSION}/supercronic-linux-${arch}"; \
    wget -q -O /usr/local/bin/supercronic "${url}"; \
    echo "${sha1}  /usr/local/bin/supercronic" | sha1sum -c -; \
    chmod 0755 /usr/local/bin/supercronic; \
    apk del .fetch-deps

COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Default: run backup daily at 2:00 AM
ENV BACKUP_CRON="0 2 * * *"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /backups \
    && touch /var/log/backup.log \
    && chown -R postgres:postgres \
      /backups \
      /var/log/backup.log \
      /usr/local/bin/backup.sh \
      /usr/local/bin/entrypoint.sh

USER postgres

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
