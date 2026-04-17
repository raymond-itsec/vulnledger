#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

usage() {
  cat <<'EOF'
Usage: ./scripts/switch-runtime-mode.sh <dev|prod>
EOF
}

mode=${1:-}
case "$mode" in
  dev|prod) ;;
  *)
    usage
    exit 1
    ;;
esac

if [ ! -f .env ]; then
  cp .env.example .env
fi

tmp_file=$(mktemp)
awk -v value="$mode" '
BEGIN { updated = 0 }
/^FINDINGS_RUNTIME_MODE=/ {
  print "FINDINGS_RUNTIME_MODE=" value
  updated = 1
  next
}
{ print }
END {
  if (!updated) {
    print "FINDINGS_RUNTIME_MODE=" value
  }
}
' .env > "$tmp_file"
mv "$tmp_file" .env

./scripts/cleanup-runtime-switch.sh

printf '%s\n' "Set FINDINGS_RUNTIME_MODE=$mode in .env"
printf '%s\n' "Next step: ./scripts/first-run.sh up"
