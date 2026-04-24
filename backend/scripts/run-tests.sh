#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set (check .env)}"

TEST_DB="findings_test"
TEST_DB_URL="postgresql+asyncpg://findings:${POSTGRES_PASSWORD}@db:5432/${TEST_DB}"

compose() { docker compose "$@"; }

cleanup() {
  echo "--> dropping ${TEST_DB}"
  compose exec -T db psql -U findings -d postgres \
    -c "DROP DATABASE IF EXISTS ${TEST_DB};" >/dev/null || true
  compose exec -T backend rm -rf /app/tests /app/pytest.ini /app/.pytest_cache >/dev/null 2>&1 || true
  find backend/tests -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  rm -rf backend/.pytest_cache 2>/dev/null || true
}
trap cleanup EXIT

echo "--> ensuring services are up"
compose up -d db backend >/dev/null

echo "--> creating ${TEST_DB}"
compose exec -T db psql -U findings -d postgres \
  -c "DROP DATABASE IF EXISTS ${TEST_DB};" >/dev/null
compose exec -T db psql -U findings -d postgres \
  -c "CREATE DATABASE ${TEST_DB};" >/dev/null

echo "--> installing test deps in backend"
compose exec -T -u root backend \
  pip install --disable-pip-version-check --quiet pytest pytest-asyncio >/dev/null

echo "--> copying tests into backend"
compose cp backend/tests backend:/app/tests >/dev/null
compose cp backend/pytest.ini backend:/app/pytest.ini >/dev/null

echo "--> running pytest"
compose exec -T \
  -e PYTHONPATH=/app \
  -e TEST_DATABASE_URL="${TEST_DB_URL}" \
  backend python -m pytest tests/ -v "$@"
