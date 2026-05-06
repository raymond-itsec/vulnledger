#!/bin/sh
set -e

BACKUP_DIR="/backups"
INITIAL_BACKUP_MAX_AGE_SECONDS=86400
DEFAULT_BACKUP_CRON="0 2 * * *"
CRON_DIR="/tmp/backup-cron"
CRON_FILE="$CRON_DIR/postgres"

# Pre-flight: validate encryption configuration BEFORE the scheduler
# starts. If the operator declared that encryption is required (either
# explicitly via BACKUP_ENCRYPTION_REQUIRED=true or implicitly via
# FINDINGS_RUNTIME_MODE=production) but no passphrase file is mounted,
# fail fast with a loud banner and a non-restarting exit code so the
# operator sees the failure in `docker compose ps` instead of an
# infinite restart loop. Paired with `restart: "no"` in compose for
# this service.
BACKUP_ENCRYPTION_SECRET_FILE="${BACKUP_ENCRYPTION_SECRET_FILE:-/run/secrets/backup_encryption_passphrase}"
BACKUP_ENCRYPTION_REQUIRED="${BACKUP_ENCRYPTION_REQUIRED:-false}"
RUNTIME_MODE="${FINDINGS_RUNTIME_MODE:-development}"

if [ ! -s "$BACKUP_ENCRYPTION_SECRET_FILE" ]; then
 if [ "$BACKUP_ENCRYPTION_REQUIRED" = "true" ] || [ "$RUNTIME_MODE" = "production" ]; then
 cat >&2 <<EOF

================================================================================
 FATAL: Backup encryption is REQUIRED but no passphrase is configured.
================================================================================

 Why this fired:
 BACKUP_ENCRYPTION_REQUIRED = $BACKUP_ENCRYPTION_REQUIRED
 FINDINGS_RUNTIME_MODE = $RUNTIME_MODE
 Expected secret file = $BACKUP_ENCRYPTION_SECRET_FILE
 File state = missing or empty

 Resolution (production / encrypted backups required):

 1. Generate a strong passphrase on the host:
 openssl rand -base64 48 > ./secrets/backup_encryption_passphrase
 chmod 600 ./secrets/backup_encryption_passphrase

 2. STORE THE PASSPHRASE IN YOUR PASSWORD MANAGER.
 Without it, encrypted backups cannot be restored. There is no
 recovery path if you lose this passphrase.

 3. Restart the backup container:
 docker compose up -d --force-recreate backup

 Alternative (development only - leaves backups UNENCRYPTED on disk):

 Add to .env on the host:
 BACKUP_ENCRYPTION_REQUIRED=false
 FINDINGS_RUNTIME_MODE=development

 Then: docker compose up -d --force-recreate backup

 This container is exiting with code 78 (configuration error) and
 WILL NOT RESTART. The rest of the stack continues running, but no
 backups are being created until this is resolved.

================================================================================

EOF
 exit 78
 fi
fi


latest_backup_age_seconds() {
 latest_file=$(ls -1t "$BACKUP_DIR"/findings_*.sql.gz* 2>/dev/null | head -n 1 || true)
 if [ -z "$latest_file" ]; then
 echo ""
 return 0
 fi

 now_epoch=$(date +%s)
 modified_epoch=$(stat -c %Y "$latest_file" 2>/dev/null || true)
 if [ -z "$modified_epoch" ]; then
 echo ""
 return 0
 fi

 age=$((now_epoch - modified_epoch))
 if [ "$age" -lt 0 ]; then
 age=0
 fi
 echo "$age"
}

is_valid_backup_cron() {
 expr="$1"
 if [ -z "$expr" ]; then
 return 1
 fi

 # Allow only standard cron field characters to prevent command injection
 # through shell metacharacters/newlines.
 invalid_chars=$(printf '%s' "$expr" | tr -d '0123456789*/, -')
 if [ -n "$invalid_chars" ]; then
 return 1
 fi

 # Require exactly 5 schedule fields: minute hour day month weekday.
 if [ "$(printf '%s' "$expr" | awk '{print NF}')" -ne 5 ]; then
 return 1
 fi

 return 0
}

if ! is_valid_backup_cron "${BACKUP_CRON:-}"; then
 echo "[$(date)] Invalid BACKUP_CRON value; falling back to default: $DEFAULT_BACKUP_CRON"
 BACKUP_CRON="$DEFAULT_BACKUP_CRON"
fi

# Set up cron schedule for the current (non-root) postgres user.
mkdir -p "$CRON_DIR"
chmod 700 "$CRON_DIR"
printf '%s %s\n' \
 "$BACKUP_CRON" \
 "/usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" \
 > "$CRON_FILE"
chmod 600 "$CRON_FILE"

echo "[$(date)] Backup scheduler started (schedule: $BACKUP_CRON)"
latest_age=$(latest_backup_age_seconds)
if [ -z "$latest_age" ] || [ "$latest_age" -ge "$INITIAL_BACKUP_MAX_AGE_SECONDS" ]; then
 echo "[$(date)] Running initial backup..."
 /usr/local/bin/backup.sh
else
 echo "[$(date)] Skipping initial backup (latest backup age: ${latest_age}s)"
fi

# Start supercronic (non-root cron) in foreground with the generated crontab.
exec supercronic "$CRON_FILE"
