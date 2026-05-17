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

# Drop a textfile-collector metric file so node-exporter on the data
# tier surfaces backup state via vmagent. Three metrics:
#   - vl_backup_latest_timestamp_seconds: unix epoch of the most recent
#     successful backup; PromQL derives age via `time() - <metric>`.
#   - vl_backup_latest_encrypted: 1 if this backup was written
#     encrypted, 0 if plaintext.
#   - vl_backup_encryption_expected: 1 if this deployment expects
#     encrypted backups (production mode or BACKUP_ENCRYPTION_REQUIRED).
# The BackupNotEncrypted alert fires on `expected == 1 and encrypted == 0`.
# Atomic rename so a concurrent node-exporter scrape never reads a
# partial write.
#
# Wrapped in `|| ...` so a textfile-volume permission glitch can never
# kill an otherwise successful backup. The dump is what matters; the
# observability metric is a downstream signal.
TEXTFILE_DIR="${TEXTFILE_COLLECTOR_DIR:-/var/lib/node-exporter/textfile}"
if [ -d "$TEXTFILE_DIR" ]; then
    {
        NOW_EPOCH=$(date +%s)
        if [ "$ENCRYPT_BACKUP" = "true" ]; then ENC_VAL=1; else ENC_VAL=0; fi
        if [ "$BACKUP_ENCRYPTION_REQUIRED" = "true" ] || [ "$RUNTIME_MODE" = "production" ]; then
            ENC_EXPECTED=1
        else
            ENC_EXPECTED=0
        fi
        TMP_FILE=$(mktemp "$TEXTFILE_DIR/backup.prom.XXXXXX") && \
        printf '# HELP vl_backup_latest_timestamp_seconds Unix epoch of the most recent successful Postgres backup.\n# TYPE vl_backup_latest_timestamp_seconds gauge\nvl_backup_latest_timestamp_seconds{source="backup"} %s\n# HELP vl_backup_latest_encrypted Whether the most recent backup was written encrypted (1) or plaintext (0).\n# TYPE vl_backup_latest_encrypted gauge\nvl_backup_latest_encrypted{source="backup"} %s\n# HELP vl_backup_encryption_expected Whether this deployment expects encrypted backups (1) or not (0).\n# TYPE vl_backup_encryption_expected gauge\nvl_backup_encryption_expected{source="backup"} %s\n' "$NOW_EPOCH" "$ENC_VAL" "$ENC_EXPECTED" > "$TMP_FILE" && \
        mv -f "$TMP_FILE" "$TEXTFILE_DIR/backup.prom" && \
        chmod 0644 "$TEXTFILE_DIR/backup.prom"
    } || echo "[$(date)] WARN: failed to write textfile metric to $TEXTFILE_DIR (backup itself succeeded)"
fi

echo "[$(date)] Backup complete."
