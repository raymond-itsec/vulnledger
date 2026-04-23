FROM postgres:16.13-alpine3.23

RUN apk add --no-cache dcron

COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Default: run backup daily at 2:00 AM
ENV BACKUP_CRON="0 2 * * *"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /backups /var/spool/cron/crontabs \
    && touch /var/log/backup.log \
    && chown -R postgres:postgres \
      /backups \
      /var/spool/cron \
      /var/log/backup.log \
      /usr/local/bin/backup.sh \
      /usr/local/bin/entrypoint.sh

USER postgres

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
