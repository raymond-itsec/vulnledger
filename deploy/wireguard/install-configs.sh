#!/usr/bin/env bash
# install-configs.sh - scp rendered wg0.conf files to each peer's host
#                      and enable wg-quick@wg0 via systemd.
#
# Requires SSH (root or sudo-capable user) already reachable at each
# peer's public endpoint host. For cold-bootstrap (peer has no SSH yet),
# inject the rendered conf via cloud-init instead of using this script.
#
# Usage:
#   ./install-configs.sh
#   SSH_USER=ubuntu ./install-configs.sh
#
# Env overrides:
#   SSH_USER   SSH user on each peer (default: root)
#   SSH_OPTS   Extra ssh options, e.g. "-i ~/.ssh/lab_key" (default: empty)

set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
PEERS_FILE="$DIR/peers.txt"
OUT_DIR="$DIR/out"

SSH_USER="${SSH_USER:-root}"
SSH_OPTS="${SSH_OPTS:-}"

if [ ! -f "$PEERS_FILE" ]; then
  echo "ERROR: $PEERS_FILE not found." >&2
  exit 1
fi

if [ ! -d "$OUT_DIR" ]; then
  echo "ERROR: $OUT_DIR not found - run render-configs.sh (or 'make wg-render') first." >&2
  exit 1
fi

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ''|\#*) continue ;;
  esac
  set -- $line
  if [ "$#" -lt 3 ]; then
    continue
  fi
  name="$1"
  endpoint="$3"
  conf="$OUT_DIR/$name.conf"

  if [ ! -f "$conf" ]; then
    echo "  $name: SKIP (no rendered conf at $conf)"
    continue
  fi

  if [ "$endpoint" = "-" ] || [ -z "$endpoint" ]; then
    echo "  $name: SKIP (road-warrior peer; install manually on the laptop)"
    continue
  fi

  ssh_host="${endpoint%:*}"
  echo "  $name -> $SSH_USER@$ssh_host"

  scp -q $SSH_OPTS "$conf" "$SSH_USER@$ssh_host:/tmp/wg0.conf.new"
  ssh -q $SSH_OPTS "$SSH_USER@$ssh_host" '
    set -e
    sudo install -m 600 -o root -g root /tmp/wg0.conf.new /etc/wireguard/wg0.conf
    sudo rm /tmp/wg0.conf.new
    sudo systemctl enable --now wg-quick@wg0 >/dev/null
    sudo systemctl restart wg-quick@wg0 >/dev/null
  '
done < "$PEERS_FILE"

echo
echo "Done. Verify with 'sudo wg show' on each host."
echo "From your admin host (if joined to the mesh): 'ping <peer-wg-ip>' to test reachability."
