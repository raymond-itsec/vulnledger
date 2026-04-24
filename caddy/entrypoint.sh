#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  set -- caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
fi

exec "$@"
