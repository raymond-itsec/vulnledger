#!/bin/sh
set -e

# Write environment variables to a file for cron to pick up
env > /etc/environment

# Set up cron schedule
echo "$BACKUP_CRON /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" | crontab -

echo "[$(date)] Backup scheduler started (schedule: $BACKUP_CRON)"
echo "[$(date)] Running initial backup..."
/usr/local/bin/backup.sh

# Start cron in foreground
crond -f -l 2
