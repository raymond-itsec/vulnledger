#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

PROJECT_NAME_DEFAULT=$(basename "$ROOT_DIR" | tr '[:upper:]' '[:lower:]')
PROJECT_NAME_DEFAULT=$(printf "%s" "$PROJECT_NAME_DEFAULT" | tr -cd 'a-z0-9_-')

info() {
  printf '%s\n' "$*"
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    die "Neither 'docker compose' nor 'docker-compose' is installed."
  fi
}

ensure_env_file() {
  if [ ! -f .env ]; then
    cp .env.example .env
    info "Created .env from .env.example"
    warn "Review .env before starting the stack. Required secrets still need real values."
  fi
}

load_env() {
  ensure_env_file
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
}

require_non_placeholder() {
  var_name=$1
  value=$2

  if [ -z "$value" ]; then
    die "$var_name is empty in .env"
  fi

  case "$value" in
    change-this-*|your-*|example.com|admin@example.com)
      die "$var_name still uses the example placeholder in .env"
      ;;
  esac
}

port_is_busy() {
  port=$1

  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$port )" 2>/dev/null | awk 'NR > 1 { found = 1 } END { exit found ? 0 : 1 }'
    return $?
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN -P -n >/dev/null 2>&1
    return $?
  fi

  return 1
}

check_port() {
  port=$1
  label=$2

  case "$port" in
    ''|*[!0-9]*)
      die "$label must be a numeric port value"
      ;;
  esac

  if port_is_busy "$port"; then
    die "$label port $port is already in use on this host"
  fi
}

warn_existing_pgdata() {
  if ! command -v docker >/dev/null 2>&1; then
    return
  fi

  project_name=${COMPOSE_PROJECT_NAME:-$PROJECT_NAME_DEFAULT}
  volume_name="${project_name}_pgdata"

  if docker volume inspect "$volume_name" >/dev/null 2>&1; then
    warn "Existing Docker volume '$volume_name' detected."
    warn "If you changed POSTGRES_PASSWORD since the first run, use:"
    warn "  ./scripts/first-run.sh reset"
  fi
}

doctor() {
  load_env

  require_non_placeholder "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-}"
  require_non_placeholder "FINDINGS_SECRET_KEY" "${FINDINGS_SECRET_KEY:-}"
  require_non_placeholder "MINIO_ROOT_PASSWORD" "${MINIO_ROOT_PASSWORD:-}"
  require_non_placeholder "FINDINGS_INITIAL_ADMIN_PASSWORD" "${FINDINGS_INITIAL_ADMIN_PASSWORD:-}"
  require_non_placeholder "FINDINGS_INITIAL_ADMIN_EMAIL" "${FINDINGS_INITIAL_ADMIN_EMAIL:-}"

  check_port "${POSTGRES_PORT:-5432}" "POSTGRES_PORT"
  check_port "${MINIO_PORT:-9000}" "MINIO_PORT"
  check_port "${MINIO_CONSOLE_PORT:-9001}" "MINIO_CONSOLE_PORT"
  check_port "${BACKEND_PORT:-8000}" "BACKEND_PORT"
  check_port "${FRONTEND_PORT:-5173}" "FRONTEND_PORT"
  check_port "${CLAMAV_PORT:-3310}" "CLAMAV_PORT"
  check_port "${CADDY_HTTP_PORT:-80}" "CADDY_HTTP_PORT"
  check_port "${CADDY_HTTPS_PORT:-443}" "CADDY_HTTPS_PORT"

  warn_existing_pgdata
  info "Preflight checks passed."
}

usage() {
  cat <<'EOF'
Usage: ./scripts/first-run.sh <command>

Commands:
  init    Create .env from .env.example if it does not exist
  doctor  Validate common first-run prerequisites
  up      Run preflight checks, then start the stack with --build
  down    Stop the stack
  reset   Stop the stack and remove named volumes
  logs    Follow caddy, frontend, and backend logs
EOF
}

command_name=${1:-}

case "$command_name" in
  init)
    ensure_env_file
    ;;
  doctor)
    doctor
    ;;
  up)
    doctor
    compose up -d --build
    ;;
  down)
    compose down
    ;;
  reset)
    compose down -v
    ;;
  logs)
    compose logs -f caddy frontend backend
    ;;
  *)
    usage
    exit 1
    ;;
esac
