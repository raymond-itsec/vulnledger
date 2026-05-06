#!/usr/bin/env bash
# Generate WireGuard keypairs for the VulnLedger mesh.
#
# Default peers: vl-edge, vl-app, vl-data, vl-monitoring. Pass extra
# peer names as arguments to add more (e.g. add `admin` for your
# admin laptop joining the mesh).
#
# Output: keys/<peer>.priv and keys/<peer>.pub, mode 0600 / 0644
# respectively. The keys/ directory is gitignored at the repo root;
# private keys must NEVER be committed.
#
# Usage:
#   ./generate-keys.sh
#   ./generate-keys.sh admin                # add a 5th peer named admin
#   ./generate-keys.sh admin laptop2        # add two extra peers
#
# Requires: wireguard-tools (`brew install wireguard-tools` on macOS,
# `apt install wireguard-tools` / `dnf install wireguard-tools` on
# Linux).

set -eu

if ! command -v wg >/dev/null 2>&1; then
  echo "ERROR: 'wg' (wireguard-tools) is not installed." >&2
  echo "  macOS:    brew install wireguard-tools" >&2
  echo "  Debian:   sudo apt install wireguard-tools" >&2
  echo "  Fedora:   sudo dnf install wireguard-tools" >&2
  exit 1
fi

DEFAULT_PEERS="vl-edge vl-app vl-data vl-monitoring"
PEERS="$DEFAULT_PEERS $*"

OUT_DIR="$(dirname "$0")/keys"
mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

echo "Generating WireGuard keypairs into $OUT_DIR"
echo

for peer in $PEERS; do
  priv="$OUT_DIR/$peer.priv"
  pub="$OUT_DIR/$peer.pub"
  if [ -f "$priv" ] || [ -f "$pub" ]; then
    echo "  $peer  SKIP (keys already exist; delete them manually to regenerate)"
    continue
  fi
  wg genkey | tee "$priv" | wg pubkey > "$pub"
  chmod 600 "$priv"
  chmod 644 "$pub"
  pubkey=$(cat "$pub")
  echo "  $peer  pub: $pubkey"
done

echo
echo "Done. Private keys are in $OUT_DIR (mode 0600)."
echo "These must NEVER be committed. The repo's root .gitignore"
echo "covers deploy/wireguard/keys/ already."
echo
echo "Next: copy wg0.conf.template per host, substitute the placeholders,"
echo "and install at /etc/wireguard/wg0.conf (mode 0600, owner root)."
