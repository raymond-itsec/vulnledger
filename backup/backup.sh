#!/bin/sh
# Automated PostgreSQL backup script
# Retains BACKUP_RETENTION_DAYS days of backups (default: 30)

set -e

# Ensure new backup files are created with 0600 perms (owner read/write only).
# Prevents "group/other" readable backups if the container's UID maps to a
# shared host user.
umask 0077

BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_ENCRYPTION_SECRET_FILE="${BACKUP_ENCRYPTION_SECRET_FILE:-/run/secrets/backup_encryption_passphrase}"
BACKUP_ENCRYPTION_REQUIRED="${BACKUP_ENCRYPTION_REQUIRED:-false}"
RUNTIME_MODE="${FINDINGS_RUNTIME_MODE:-development}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

ENCRYPT_BACKUP=false
if [ -s "$BACKUP_ENCRYPTION_SECRET_FILE" ]; then
    ENCRYPT_BACKUP=true
elif [ "$BACKUP_ENCRYPTION_REQUIRED" = "true" ] || [ "$RUNTIME_MODE" = "production" ]; then
    echo "[$(date)] Encryption secret missing at $BACKUP_ENCRYPTION_SECRET_FILE" >&2
    exit 1
fi

if [ "$ENCRYPT_BACKUP" = "true" ]; then
    BACKUP_FILE="${BACKUP_DIR}/findings_${TIMESTAMP}.sql.gz.enc"
else
    BACKUP_FILE="${BACKUP_DIR}/findings_${TIMESTAMP}.sql.gz"
fi

echo "[$(date)] Starting backup..."

# Create backup directory if needed
mkdir -p "$BACKUP_DIR"

# Dump, compress, and optionally encrypt.
if [ "$ENCRYPT_BACKUP" = "true" ]; then
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --no-owner \
        --no-acl \
        | gzip \
        | openssl enc -aes-256-cbc -salt -pbkdf2 -pass "file:${BACKUP_ENCRYPTION_SECRET_FILE}" \
        > "$BACKUP_FILE"
else
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --no-owner \
        --no-acl \
        | gzip > "$BACKUP_FILE"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Prune old backups
DELETED=$(find "$BACKUP_DIR" -name "findings_*.sql.gz*" -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Pruned $DELETED backup(s) older than $RETENTION_DAYS days"
fi

# Drop a textfile-collector metric so node-exporter on the data tier
# surfaces backup freshness via vmagent. We expose the unix timestamp
# of the most recent successful backup; PromQL derives age via
# `time() - vl_backup_latest_timestamp_seconds`. Atomic rename so a
# concurrent node-exporter scrape never reads a partial write.
TEXTFILE_DIR="${TEXTFILE_COLLECTOR_DIR:-/var/lib/node-exporter/textfile}"
if [ -d "$TEXTFILE_DIR" ]; then
    NOW_EPOCH=$(date +%s)
    TMP_FILE=$(mktemp "$TEXTFILE_DIR/backup.prom.XXXXXX")
    printf '# HELP vl_backup_latest_timestamp_seconds Unix epoch of the most recent successful Postgres backup.\n# TYPE vl_backup_latest_timestamp_seconds gauge\nvl_backup_latest_timestamp_seconds %s\n' "$NOW_EPOCH" > "$TMP_FILE"
    mv -f "$TMP_FILE" "$TEXTFILE_DIR/backup.prom"
    chmod 0644 "$TEXTFILE_DIR/backup.prom"
fi

echo "[$(date)] Backup complete."
