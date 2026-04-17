#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

info() {
  printf '%s\n' "$*"
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
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

attempt_cleanup() {
  info "Cleaning frontend build artifacts"
  rm -rf frontend/.svelte-kit frontend/build frontend/node_modules/.vite

  info "Cleaning Python bytecode caches"
  find backend -type d -name '__pycache__' -prune -exec rm -rf {} +
}

attempt_docker_chown() {
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi

  # TODO: Run app containers as non-root by default to avoid bind-mount ownership drift.
  uid=$(id -u)
  gid=$(id -g)

  docker run --rm \
    -v "$ROOT_DIR:/workspace" \
    alpine:3.21 \
    sh -c "chown -R $uid:$gid /workspace/backend /workspace/frontend" >/dev/null 2>&1
}

info "Stopping running containers before mode switch cleanup"
compose down --remove-orphans >/dev/null 2>&1 || true

cleanup_error_log=$(mktemp)
if ! attempt_cleanup 2>"$cleanup_error_log"; then
  warn "Cleanup hit a permissions issue. Trying to repair bind-mount ownership with Docker."
  if attempt_docker_chown && attempt_cleanup 2>"$cleanup_error_log"; then
    info "Ownership repair succeeded"
  else
    warn "Could not remove some files. Run this once, then retry:"
    warn "sudo chown -R $(id -u):$(id -g) backend frontend"
    cat "$cleanup_error_log" >&2
  fi
fi
rm -f "$cleanup_error_log"

if command -v docker >/dev/null 2>&1; then
  info "Pruning dangling Docker images"
  docker image prune -f >/dev/null 2>&1 || true
fi

info "Runtime switch cleanup complete"
