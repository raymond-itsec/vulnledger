#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

info() {
  printf '%s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

find_python() {
  if [ -n "${FINDINGS_PYTHON_BIN:-}" ]; then
    printf '%s\n' "$FINDINGS_PYTHON_BIN"
    return 0
  fi

  for candidate in python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

PYTHON_BIN=$(find_python) || die "Python 3.12+ is required. Install Python 3.12 or set FINDINGS_PYTHON_BIN."

"$PYTHON_BIN" - <<'PY' || die "Selected interpreter must be Python 3.12 or newer."
import sys

if sys.version_info < (3, 12):
    raise SystemExit(1)
PY

VENV_DIR=$(mktemp -d "${TMPDIR:-/tmp}/vulnledger-backend-check.XXXXXX")
cleanup() {
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT INT TERM

info "Using Python: $PYTHON_BIN"
info "Creating temporary virtualenv: $VENV_DIR"

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -r backend/requirements.txt

PYTHONPYCACHEPREFIX="$VENV_DIR/pycache" "$VENV_DIR/bin/python" -m compileall backend/app

PYTHONPATH="$ROOT_DIR/backend" "$VENV_DIR/bin/python" - <<'PY'
from app.main import app
from app.services.auth import hash_password, verify_password
from app.services.reports import generate_pdf
from weasyprint import HTML

assert app is not None
hashed = hash_password("verification-password")
assert verify_password("verification-password", hashed)
assert callable(generate_pdf)
assert HTML is not None
print("Backend verification passed.")
PY
