# Operations

Day-two material: backups, monitoring, logging, templates.

## Backup & recovery

### Automatic backups

The `backup` service runs scheduled PostgreSQL dumps:

```bash
# Check backup status
docker compose logs backup

# List existing backups
docker compose exec backup ls -la /backups/

# Run a manual backup
docker compose exec backup /usr/local/bin/backup.sh
```

Schedule and retention are controlled by `BACKUP_CRON` (default daily at 02:00) and `BACKUP_RETENTION_DAYS` (default 30). In production runtime mode, the backup container will refuse to start unless an encryption passphrase is mounted. See [Configuration](configuration.md#backup-configuration) for the full set of backup env vars.

### Manual backup

```bash
# Dump database directly
docker compose exec db pg_dump -U findings findings | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Stop the backend first
docker compose stop backend

# Restore from backup
gunzip -c backup_20260415.sql.gz | docker compose exec -T db psql -U findings findings

# Restart
docker compose start backend
```

For an encrypted backup (`*.sql.gz.enc`), prepend the openssl decrypt step:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in backup_20260501.sql.gz.enc \
  -pass file:./secrets/backup_encryption_passphrase \
  | gunzip \
  | docker compose exec -T db psql -U findings findings
```

### Object storage backup

File attachments and generated reports are stored in SeaweedFS. Back up the `seaweedfs_data` volume separately:

```bash
docker run --rm -v vulnledger_seaweedfs_data:/data -v /host/backup:/backup alpine \
  tar czf /backup/seaweedfs_$(date +%Y%m%d).tar.gz /data
```

For production scale, prefer SeaweedFS native replication or upload to a separate object-storage bucket on a different provider.

## Monitoring & logging

### Structured logs

The backend emits one JSON object per log line to stdout. Level is controlled by `FINDINGS_LOG_LEVEL` (`DEBUG | INFO | WARNING | ERROR | CRITICAL`, case-insensitive; default `INFO`). Uvicorn access and error logs share the same JSON format.

```bash
docker compose logs -f backend | jq
```

Every service uses the `json-file` driver with rotation at 10 MB × 5 files to keep disk use bounded.

### Healthchecks and startup order

`docker-compose.yml` defines healthchecks for `db` (`pg_isready`), `seaweedfs`, `clamav`, and `caddy`. The backend declares `depends_on` with `condition: service_healthy` against `db` and `seaweedfs`, so it does not attempt migrations or accept traffic until its dependencies are ready. `docker compose ps` reflects per-service health, and crashed containers restart via `restart: unless-stopped` (except `backup`, which uses `restart: "no"` so a config error doesn't loop).

### Recommended observability stack

For trending, alerting, and 1-year retention, the planned stack is:

- **VictoriaMetrics** as the time-series database (drop-in Prometheus replacement, ~10x better compression at long retention)
- **vmagent** scraping per-host exporters
- **vmalert + Alertmanager** for evaluation and Slack delivery
- **Grafana** for dashboards (internal SSO + a public anonymous status board)
- **Loki + promtail** for log aggregation

Set this up as part of moving to the multi-host topology described in [Deployment](deployment.md).

### Deploy workflow & config refresh

> **Applies to v0.3.0 and later.** Earlier releases used a single root `docker-compose.yml` without the per-tier Makefile; operators on those versions need the manual `docker compose up -d --force-recreate <service>` workaround described in the last paragraph of this section.

`make allinone-up` (and `make multihost-{samedc,crossdc}-up`) does three things in order:

1. `docker compose up -d --build --remove-orphans` — rebuilds local images on every invocation and creates / updates containers whose configuration changed.
2. `docker compose up -d --no-deps --force-recreate ...` against a fixed list of services that have **single-file bind mounts** — see below.
3. `docker kill -s HUP <alertmanager>` — graceful Alertmanager config reload after the rendered config refresh.

The second step exists because of a Docker behaviour that bites silently: when a container has a bind mount of a single file (not a directory), Docker captures the host file's **inode** at container *create* time. Git updates files via rename-replace for atomicity, so after a `git pull` the path on disk points to a new inode while the running container's bind mount remains attached to the old (now-unlinked) inode. The container then serves stale content forever, even though `docker inspect` shows the bind mount as "attached" and the host path as correct.

The services affected (every one bind-mounting a single file managed by git) are listed in the `FILE_MOUNT_SERVICES` variable at the top of `deploy/Makefile`:

- **caddy** → `Caddyfile`
- **vmagent-{edge,app,data,monitoring}** → `monitoring/vmagent/scrape-<tier>.yml`
- **alertmanager-init** → `monitoring/alertmanager/config.yml.tmpl`
- **loki** → `monitoring/loki/config.yml`
- **promtail-{edge,app,data,monitoring}** → `monitoring/promtail/config.yml`

Directory bind mounts are not affected (vmalert rules, Grafana provisioning, dashboards) — directory mounts re-resolve children automatically. The `Makefile` force-recreate list excludes them.

Cost of the second step: ~10 seconds of recreate time per `make allinone-up`. The trade-off is firmly worth it; without it, edits to any of the listed config files appear to land but silently don't take effect.

If you ever bypass the Makefile and call `docker compose up -d` directly, remember to also run:

```
docker compose -p vulnledger ... up -d --no-deps --force-recreate caddy vmagent-edge vmagent-app vmagent-data vmagent-monitoring alertmanager-init loki promtail-edge promtail-app promtail-data promtail-monitoring
```

If you add a new service that bind-mounts a single config file, add it to `FILE_MOUNT_SERVICES` so the same protection applies.

## Finding templates

The application ships with **25 built-in finding templates** organized by category:

| Category | Templates |
|---|---|
| **Injection** | SQL Injection, XSS (Reflected, Stored, DOM), Command Injection, SSTI |
| **Authentication** | Weak Password Policy, Missing MFA, Session Fixation, Insecure Token Storage |
| **Access Control** | IDOR, Privilege Escalation, Missing Function-Level Access Control, CORS Misconfiguration |
| **Cryptography** | Weak Hashing, Insecure TLS, Hardcoded Secrets, Insufficient Entropy |
| **Misconfiguration** | Verbose Errors, Missing Security Headers, Directory Listing |
| **Other** | SSRF, CSRF, Open Redirect, Vulnerable Dependency |

Templates are defined as YAML files in `backend/templates/` and synced on startup. Example:

```yaml
id: builtin-sql-injection
name: SQL Injection
category: Injection
risk_level: high
title: "SQL Injection in [component]"
description: |
  The application constructs SQL queries using unsanitized user input...
impact: |
  An attacker can read, modify, or delete arbitrary data...
recommendation: |
  Use parameterized queries (prepared statements)...
references:
  - CWE-89
  - https://owasp.org/Top10/A03_2021-Injection/
```

### Custom templates

Create custom templates through the UI (Templates → New Template) or add YAML files to `backend/templates/custom/`.
