FROM postgres:17.10-alpine3.23@sha256:0f8b50ac606e525bc7a34f1f45219856dc15f0d37967d1c30ad0863e19fe5cb3

ARG TARGETARCH
ARG SUPERCRONIC_VERSION=0.2.45
ARG SUPERCRONIC_SHA1_AMD64=e894b193bea75a5ee644e700c59e30eedc804cf7
ARG SUPERCRONIC_SHA1_ARM64=20ce6dace414a64f0632f4092d6d3745db6085ad

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
