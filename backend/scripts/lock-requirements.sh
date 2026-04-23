#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "python3.12 is required to regenerate backend/requirements.lock.txt" >&2
  exit 1
fi

python3.12 -m pip install --upgrade pip pip-tools
python3.12 -m piptools compile \
  --resolver=backtracking \
  --strip-extras \
  --output-file backend/requirements.lock.txt \
  backend/requirements.txt

echo "Updated backend/requirements.lock.txt"
