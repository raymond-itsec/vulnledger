# VulnLedger deploy Makefile.
#
# Targets:
#   make allinone-up      Bring up all 4 tiers on the local Docker daemon
#                         (dev box). Loads deploy/profiles/allinone.env first,
#                         then the project-root .env (overrides allinone).
#   make allinone-down    Tear down the allinone stack (preserves volumes).
#   make multihost-up     (Phase 5+) Provision + deploy 4 ESXi VMs.
#   make multihost-down   (Phase 5+) Stop containers on all 4 VMs.
#   make logs SERVICE=    Tail logs from a specific service in allinone mode.
#   make wg-status        (Phase 4+) Show WireGuard mesh peer status.
#   make help             This message.
#
# The compose tier files (deploy/compose/{edge,app,data,monitoring}.yml)
# are designed to work in BOTH modes by swapping the env profile.
# Service discovery, port bindings, and Caddy upstreams differ; the
# compose YAML stays identical.

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
COMPOSE_DIR := $(ROOT)/deploy/compose
PROFILES_DIR := $(ROOT)/deploy/profiles

ALLINONE_FILES := \
	-f $(COMPOSE_DIR)/data.yml \
	-f $(COMPOSE_DIR)/app.yml \
	-f $(COMPOSE_DIR)/edge.yml \
	-f $(COMPOSE_DIR)/monitoring.yml

# Env-file order matters: profile loads first, project .env overrides.
# Compose's --env-file repeated is supported in Compose v2.21+.
ALLINONE_ENV := \
	--env-file $(PROFILES_DIR)/allinone.env \
	--env-file $(ROOT)/.env

# Single project name keeps containers grouped (e.g. `vulnledger-backend-1`).
PROJECT := vulnledger

.DEFAULT_GOAL := help

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: allinone-up
allinone-up: ## Bring up all 4 tiers on the local Docker daemon
	@test -f $(ROOT)/.env || { echo "ERROR: $(ROOT)/.env not found. Copy .env.example to .env and fill in secrets."; exit 1; }
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) up -d --remove-orphans

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
logs: ## Tail logs from a service in allinone mode (usage: make logs SERVICE=backend)
	@test -n "$(SERVICE)" || { echo "ERROR: pass SERVICE= (e.g. make logs SERVICE=backend)"; exit 1; }
	docker compose -p $(PROJECT) $(ALLINONE_ENV) $(ALLINONE_FILES) logs -f $(SERVICE)

.PHONY: multihost-up
multihost-up: ## (Phase 5+) Provision + deploy 4 ESXi VMs
	@echo "Multihost deploy not implemented yet - lands in Phase 5."
	@echo "See ~/.claude/.../memory/local_validation_lab.md for design."
	@exit 1

.PHONY: multihost-down
multihost-down: ## (Phase 5+) Stop containers on all 4 VMs
	@echo "Multihost deploy not implemented yet - lands in Phase 5."
	@exit 1

.PHONY: wg-status
wg-status: ## (Phase 4+) Show WireGuard mesh peer status
	@echo "WireGuard mesh not implemented yet - lands in Phase 4."
	@echo "See ~/.claude/.../memory/local_validation_lab.md for design."
	@exit 1
