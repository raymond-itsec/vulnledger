#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

NO_CACHE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    -nocache|-clean)
      NO_CACHE=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/redeploy.sh [-nocache|-clean]

Options:
  -nocache   Build images with --no-cache
  -clean     Alias for -nocache
EOF
      exit 0
      ;;
    *)
      printf 'ERROR: Unknown option: %s\n' "$1" >&2
      printf 'Usage: ./scripts/redeploy.sh [-nocache|-clean]\n' >&2
      exit 1
      ;;
  esac
  shift
done

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

require_clean_git_tree() {
  if ! command -v git >/dev/null 2>&1; then
    die "git is required for redeploy"
  fi

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    die "Redeploy must run inside a git work tree"
  fi

  if ! git diff --quiet --ignore-submodules -- || ! git diff --cached --quiet --ignore-submodules --; then
    die "Tracked git changes detected. Commit/stash/restore first, then rerun redeploy."
  fi
}

sync_repo() {
  require_clean_git_tree
  info "Pulling latest changes (fast-forward only)"
  git pull --ff-only
}

require_min_length() {
  var_name=$1
  value=$2
  min_len=$3

  if [ -z "$value" ]; then
    die "$var_name is empty in .env"
  fi

  value_len=$(printf '%s' "$value" | wc -c | tr -d '[:space:]')
  if [ "$value_len" -lt "$min_len" ]; then
    die "$var_name must be at least ${min_len} characters (got ${value_len}). Example: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
  fi
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

  info "Backend did not become ready within timeout. Recent backend logs:"
  compose logs --tail 120 backend || true
  die "Backend failed readiness check. See logs above."
}

build_service() {
  service=$1
  if [ "$NO_CACHE" -eq 1 ]; then
    info "Building ${service} image (--pull --no-cache)"
    compose build --pull --no-cache "$service"
  else
    info "Building ${service} image (--pull, cache enabled)"
    compose build --pull "$service"
  fi
}

sync_repo
load_env
require_min_length "FINDINGS_SECRET_KEY" "${FINDINGS_SECRET_KEY:-}" 32

build_service backend

info "Starting required infrastructure services"
compose up -d db minio clamav

info "Running DB migrations first"
compose run --rm --no-deps backend alembic upgrade head

info "Deploying backend"
compose up -d --force-recreate backend

wait_for_backend

build_service frontend
build_service backup
build_service caddy

info "Deploying frontend and edge services"
compose up -d --force-recreate frontend caddy backup

info "Redeploy complete"
