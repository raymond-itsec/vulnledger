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

compose() {
  ensure_env_file
  if docker compose version >/dev/null 2>&1; then
    docker compose --project-directory "$ROOT_DIR" -f "$ROOT_DIR/docker-compose.yml" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose --project-directory "$ROOT_DIR" -f "$ROOT_DIR/docker-compose.yml" "$@"
  else
    die "Neither 'docker compose' nor 'docker-compose' is installed."
  fi
}

ensure_env_file() {
  if [ ! -f .env ]; then
    cp .env.example .env
    info "Created .env from .env.example"
    die "Review .env first, then rerun redeploy."
  fi
}

load_env() {
  ensure_env_file
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

wait_for_backend() {
  host_port=${BACKEND_PORT:-8000}
  backend_url="http://127.0.0.1:${host_port}/openapi.json"
  max_attempts=60
  attempt=1

  info "Waiting for backend readiness at ${backend_url}"
  while [ "$attempt" -le "$max_attempts" ]; do
    if have_cmd curl; then
      if curl -fsS --max-time 2 "$backend_url" >/dev/null 2>&1; then
        info "Backend is ready"
        return 0
      fi
    elif have_cmd wget; then
      if wget -q -T 2 -O /dev/null "$backend_url" >/dev/null 2>&1; then
        info "Backend is ready"
        return 0
      fi
    else
      die "Neither curl nor wget is installed; cannot verify backend readiness."
    fi

    sleep 2
    attempt=$((attempt + 1))
  done

  die "Backend did not become ready within timeout. Check: ./scripts/first-run.sh logs"
}

load_env

info "Building backend image"
compose build backend

info "Starting required infrastructure services"
compose up -d db minio clamav

info "Running DB migrations first"
compose run --rm --no-deps backend alembic upgrade head

info "Deploying backend"
compose up -d backend

wait_for_backend

info "Building frontend image"
compose build frontend

info "Deploying frontend and edge services"
compose up -d frontend caddy backup

info "Redeploy complete"
