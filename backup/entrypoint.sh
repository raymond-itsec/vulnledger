#!/bin/sh
set -e

BACKUP_DIR="/backups"
INITIAL_BACKUP_MAX_AGE_SECONDS=86400
DEFAULT_BACKUP_CRON="0 2 * * *"
CRON_DIR="/tmp/backup-cron"
CRON_FILE="$CRON_DIR/postgres"

latest_backup_age_seconds() {
  latest_file=$(ls -1t "$BACKUP_DIR"/findings_*.sql.gz 2>/dev/null | head -n 1 || true)
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
