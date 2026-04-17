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

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

attempt_cache_cleanup() {
  info "Cleaning frontend cache artifacts"
  rm -rf frontend/.svelte-kit frontend/build frontend/node_modules/.vite

  info "Cleaning backend Python cache artifacts"
  find backend -type d -name '__pycache__' -prune -exec rm -rf {} +
  find backend -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
}

attempt_docker_chown() {
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi

  uid=$(id -u)
  gid=$(id -g)

  docker run --rm \
    -v "$ROOT_DIR:/workspace" \
    alpine:3.21 \
    sh -c "chown -R $uid:$gid /workspace/backend /workspace/frontend" >/dev/null 2>&1
}

if ! command -v git >/dev/null 2>&1; then
  die "git is required"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  die "This script must run inside a git work tree"
fi

if ! git diff --quiet --ignore-submodules -- || ! git diff --cached --quiet --ignore-submodules --; then
  die "Tracked changes detected. Commit/stash/restore first, then rerun."
fi

cleanup_error_log=$(mktemp)
if ! attempt_cache_cleanup 2>"$cleanup_error_log"; then
  warn "Cache cleanup hit a permissions issue. Trying ownership repair via Docker."
  if attempt_docker_chown && attempt_cache_cleanup 2>"$cleanup_error_log"; then
    info "Ownership repair succeeded"
  else
    warn "Could not clean some cache files. Run this once, then rerun:"
    warn "sudo chown -R $(id -u):$(id -g) backend frontend"
    cat "$cleanup_error_log" >&2
  fi
fi
rm -f "$cleanup_error_log"

info "Pulling latest changes (fast-forward only)"
git pull --ff-only

info "Retest sync complete"
