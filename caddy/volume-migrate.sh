#!/bin/sh
set -eu

RUNTIME_UID="${CADDY_RUNTIME_UID:-10001}"
RUNTIME_GID="${CADDY_RUNTIME_GID:-10001}"
MARKER_PATH="/config/.vulnledger-caddy-owner-${RUNTIME_UID}-${RUNTIME_GID}"

mkdir -p /data /config

if [ -f "$MARKER_PATH" ]; then
  echo "[caddy-volume-migrate] Ownership already prepared (marker: $MARKER_PATH)."
  exit 0
fi

echo "[caddy-volume-migrate] Applying one-time ownership migration for /data and /config."
chown -R "${RUNTIME_UID}:${RUNTIME_GID}" /data /config
touch "$MARKER_PATH"
chown "${RUNTIME_UID}:${RUNTIME_GID}" "$MARKER_PATH"
echo "[caddy-volume-migrate] Migration complete."
