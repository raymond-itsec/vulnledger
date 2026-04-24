#!/bin/sh
set -eu

# Ensure persistent Caddy volumes are writable by the runtime user.
# Only touch mounted writable volumes here (container rootfs is read-only).
mkdir -p /data /config
chown -R 10001:10001 /data /config

if [ "$#" -eq 0 ]; then
  set -- caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
fi

exec su-exec 10001:10001 "$@"
