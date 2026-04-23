FROM postgres:16.13-alpine3.23@sha256:4e6e670bb069649261c9c18031f0aded7bb249a5b6664ddec29c013a89310d50

ARG TARGETARCH
ARG SUPERCRONIC_VERSION=0.2.44
ARG SUPERCRONIC_SHA1_AMD64=6eb0a8e1e6673675dc67668c1a9b6409f79c37bc
ARG SUPERCRONIC_SHA1_ARM64=6c6cba4cde1dd4a1dd1e7fb23498cde1b57c226c

RUN apk add --no-cache ca-certificates wget openssl

COPY fetch-supercronic.sh /usr/local/bin/fetch-supercronic.sh
RUN chmod +x /usr/local/bin/fetch-supercronic.sh

COPY vendor/ /opt/vendor/
RUN /usr/local/bin/fetch-supercronic.sh

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
