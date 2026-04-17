#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

info() {
  printf '%s\n' "$*"
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    return 0
  fi
}

info "Stopping running containers before mode switch cleanup"
compose down --remove-orphans >/dev/null 2>&1 || true

info "Cleaning frontend build artifacts"
rm -rf frontend/.svelte-kit frontend/build frontend/node_modules/.vite

info "Cleaning Python bytecode caches"
find backend -type d -name '__pycache__' -prune -exec rm -rf {} +

if command -v docker >/dev/null 2>&1; then
  info "Pruning dangling Docker images"
  docker image prune -f >/dev/null 2>&1 || true
fi

info "Runtime switch cleanup complete"
