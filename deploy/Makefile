# VulnLedger deploy Makefile.
#
# Targets group by deployment shape (allinone / multihost-samedc /
# multihost-crossdc). The compose tier files
# (deploy/compose/{edge,app,data,monitoring}.yml) are shape-agnostic;
# only the env profile differs.
#
# See docs/deployment.md for what each shape means and the
# connectivity contract operators must satisfy.
#
#   make help                    Show this table
#   make allinone-up             Single-host: all 4 tiers on one Docker daemon
#   make allinone-down           Tear down (preserves volumes)
#   make allinone-build          Rebuild local images
#   make allinone-ps             Service status
#   make allinone-config         Render merged compose config (debug)
#   make logs SERVICE=backend    Tail logs from a service in allinone
#   make multihost-samedc-up     One tier on this host, same-DC profile
#                                (run on each of the 4 hosts; tier auto-
#                                detected from hostname prefix vl-)
#   make multihost-samedc-down   Tear down this host's tier
#   make multihost-crossdc-up    Same as samedc but for cross-DC profile
#                                (WireGuard mesh is the primary network)
#   make multihost-crossdc-down  Tear down this host's tier
#   make wg-keys                 Generate WireGuard keypairs (cross-DC only)
#   make wg-status               Show WG mesh peer status (placeholder)

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
COMPOSE_DIR := $(ROOT)/deploy/compose
PROFILES_DIR := $(ROOT)/deploy/profiles
WG_DIR := $(ROOT)/deploy/wireguard

ALLINONE_FILES := \
	-f $(COMPOSE_DIR)/data.yml \
	-f $(COMPOSE_DIR)/app.yml \
	-f $(COMPOSE_DIR)/edge.yml \
	-f $(COMPOSE_DIR)/monitoring.yml

# Services with single-file bind mounts. Docker captures the host
# file's inode at container CREATE time; git updates files via rename-
# replace, so after a pull the host path points to a new inode while
# the running container's bind mount stays attached to the old (now-
# unlinked) one. The container then serves stale content silently
# until manually recreated. We force-recreate these services on every
# `up` so a `git pull` always propagates. Caddy hit this 2026-05-08;
# every service in this list has the same vulnerability.
#
# Excluded from this list: backend's .env / docker-compose.yml mounts
# (reference paths only, never read at runtime) and any service that
# bind-mounts a directory (directory mounts re-resolve children
# automatically and don't have the inode-pinning issue).
FILE_MOUNT_SERVICES := \
	caddy \
	vmagent-edge vmagent-app vmagent-data vmagent-monitoring \
	alertmanager-init \
	loki \
	promtail-edge promtail-app promtail-data promtail-monitoring

# Env-file order matters: versions first (image pins; deployment-shape
# agnostic), then profile, then project .env (operator overrides).
# Compose's repeated --env-file is supported in Compose v2.21+.
# Loading versions.env first means a typo in a profile or .env can't
# silently downgrade an image tag.
VERSIONS_ENV := --env-file $(PROFILES_DIR)/versions.env

ALLINONE_ENV := \
	$(VERSIONS_ENV) \
	--env-file $(PROFILES_DIR)/allinone.env \
	--env-file $(ROOT)/.env

# Multihost env: versions, then per-shape profile, then per-deploy override.
MULTIHOST_SAMEDC_ENV := \
	$(VERSIONS_ENV) \
	--env-file $(PROFILES_DIR)/multihost-samedc.env \
	--env-file $(ROOT)/.env
MULTIHOST_CROSSDC_ENV := \
	$(VERSIONS_ENV) \
	--env-file $(PROFILES_DIR)/multihost-crossdc.env \
	--env-file $(ROOT)/.env

# In multihost mode each host runs ONE tier file. Auto-detect from
# hostname prefix vl-: vl-data runs data.yml, vl-app runs app.yml, etc.
# Override with `TIER=data make multihost-samedc-up` if your hostnames
# don't follow the vl- convention.
TIER ?= $(shell h=$$(hostname -s); case $$h in vl-edge) echo edge;; vl-app) echo app;; vl-data) echo data;; vl-monitoring) echo monitoring;; *) echo "";; esac)

# Single project name keeps containers grouped (e.g. `vulnledger-backend-1`).
PROJECT := vulnledger

.DEFAULT_GOAL := help

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------------------------------------------------------------------
# Allinone (single host running all 4 tiers).
# ---------------------------------------------------------------------

.PHONY: allinone-up
allinone-up: ## Bring up all 4 tiers on a single Docker daemon
	@test -f $(ROOT)/.env || { echo "ERROR: $(ROOT)/.env not found. Copy .env.example to .env and fill in secrets."; exit 1; }
	@# `--build` makes compose re-evaluate Dockerfiles on every up, so
	@# local source changes to backend / frontend / caddy / backup land
	@# automatically. With the layer cache this is a no-op (~1s) when
	@# nothing changed; when something did change, the rebuilt image's
	@# new digest triggers an automatic container recreate.
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) up -d --build --remove-orphans
	@# Force-recreate services with single-file bind mounts so a recent
	@# `git pull` (which rename-replaces files, breaking Docker's inode-
	@# based bind mount) actually propagates. Without this every config
	@# edit to the Caddyfile / scrape configs / Loki config / promtail
	@# config / alertmanager template silently keeps serving stale
	@# content. See FILE_MOUNT_SERVICES comment for the full rationale.
	@# This also covers the alertmanager-init re-render: recreating it
	@# re-runs envsubst against the current env vars.
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) up -d --no-deps --force-recreate $(FILE_MOUNT_SERVICES)
	@# SIGHUP alertmanager so it picks up the freshly-rendered config
	@# without losing in-flight alert state.
	@docker kill -s HUP $(PROJECT)-alertmanager-1 >/dev/null 2>&1 || true
	@echo "alertmanager: SIGHUP sent (config reloaded from re-rendered template)"

.PHONY: allinone-build
allinone-build: ## Rebuild local images (backend, frontend, caddy, backup)
	@test -f $(ROOT)/.env || { echo "ERROR: $(ROOT)/.env not found."; exit 1; }
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) build

.PHONY: allinone-down
allinone-down: ## Tear down the allinone stack (preserves volumes)
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) down --remove-orphans

.PHONY: allinone-ps
allinone-ps: ## Show service status in allinone mode
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) ps

.PHONY: allinone-config
allinone-config: ## Render the merged compose config (debug)
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) config

.PHONY: logs
logs: ## Tail logs from a service in allinone (usage: make logs SERVICE=backend)
	@test -n "$(SERVICE)" || { echo "ERROR: pass SERVICE= (e.g. make logs SERVICE=backend)"; exit 1; }
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) logs -f $(SERVICE)

# ---------------------------------------------------------------------
# Multihost: SAME-DC mode (4 hosts, shared private network).
# Run on EACH host; the host runs the tier matching its name.
#
# `--profile multihost` activates per-tier node-exporter / cAdvisor
# sidecars that are skipped in allinone (where they would just
# duplicate the monitoring tier's). See edge.yml for the full
# rationale on each profile-tagged service.
# ---------------------------------------------------------------------

.PHONY: multihost-samedc-up
multihost-samedc-up: ## Bring up THIS host's tier in same-DC multihost mode
	@test -n "$(TIER)" || { echo "ERROR: could not detect tier from hostname (expected vl-edge / vl-app / vl-data / vl-monitoring). Pass TIER= explicitly."; exit 1; }
	@test -f $(ROOT)/.env || { echo "ERROR: $(ROOT)/.env not found. Copy .env.example to .env and fill in secrets."; exit 1; }
	@# Same alertmanager-init re-render trick as allinone-up. Only
	@# applies when bringing up the monitoring tier; harmless no-op on
	@# the other tiers (the container doesn't exist there).
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_SAMEDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml up -d --build --remove-orphans
	@# Force-recreate file-mount services that exist in this tier to
	@# refresh bind-mount inodes after a git pull. compose ignores
	@# unknown services in --force-recreate, so passing the full list
	@# is safe across all four tier files.
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_SAMEDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml up -d --no-deps --force-recreate $(FILE_MOUNT_SERVICES) 2>/dev/null || true
	@docker kill -s HUP $(PROJECT)-alertmanager-1 >/dev/null 2>&1 || true

.PHONY: multihost-samedc-down
multihost-samedc-down: ## Tear down THIS host's tier (same-DC)
	@test -n "$(TIER)" || { echo "ERROR: pass TIER= (edge / app / data / monitoring)."; exit 1; }
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_SAMEDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml down --remove-orphans

# ---------------------------------------------------------------------
# Multihost: CROSS-DC mode (4 hosts, geographically distributed).
# WireGuard mesh is the primary network. Run on EACH host.
# ---------------------------------------------------------------------

.PHONY: multihost-crossdc-up
multihost-crossdc-up: ## Bring up THIS host's tier in cross-DC multihost mode
	@test -n "$(TIER)" || { echo "ERROR: could not detect tier from hostname (expected vl-edge / vl-app / vl-data / vl-monitoring). Pass TIER= explicitly."; exit 1; }
	@test -f $(ROOT)/.env || { echo "ERROR: $(ROOT)/.env not found. Copy .env.example to .env and fill in secrets."; exit 1; }
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_CROSSDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml up -d --build --remove-orphans
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_CROSSDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml up -d --no-deps --force-recreate $(FILE_MOUNT_SERVICES) 2>/dev/null || true
	@docker kill -s HUP $(PROJECT)-alertmanager-1 >/dev/null 2>&1 || true

.PHONY: multihost-crossdc-down
multihost-crossdc-down: ## Tear down THIS host's tier (cross-DC)
	@test -n "$(TIER)" || { echo "ERROR: pass TIER= (edge / app / data / monitoring)."; exit 1; }
	docker compose -p $(PROJECT) --profile multihost $(MULTIHOST_CROSSDC_ENV) -f $(COMPOSE_DIR)/$(TIER).yml down --remove-orphans

# ---------------------------------------------------------------------
# WireGuard mesh (cross-DC only).
# ---------------------------------------------------------------------

.PHONY: wg-keys
wg-keys: ## Generate WireGuard keypairs into deploy/wireguard/keys/
	@bash $(WG_DIR)/generate-keys.sh

.PHONY: wg-render
wg-render: ## Render per-host wg0.conf into deploy/wireguard/out/ (needs peers.txt + keys)
	@bash $(WG_DIR)/render-configs.sh

.PHONY: wg-bootstrap
wg-bootstrap: ## wg-keys + wg-render in sequence (the usual setup path)
	@bash $(WG_DIR)/generate-keys.sh
	@echo
	@bash $(WG_DIR)/render-configs.sh

.PHONY: wg-install
wg-install: ## scp rendered configs to each peer + enable wg-quick (requires SSH access)
	@bash $(WG_DIR)/install-configs.sh

.PHONY: wg-status
wg-status: ## Show WireGuard mesh peer status (placeholder)
	@echo "Run 'sudo wg show' on each host."
	@echo "Aggregating mesh status across all 4 hosts is a follow-up."
