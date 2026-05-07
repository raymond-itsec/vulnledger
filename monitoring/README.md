# Observability stack configuration

Config files for the observability stack defined in
`deploy/compose/monitoring.yml` and the per-tier sidecars in
`deploy/compose/{edge,app,data}.yml`.

## Directory layout

```
monitoring/
├── vmagent/
│   ├── scrape-edge.yml          # vmagent on vl-edge: scrapes caddy + node-exporter + cadvisor
│   ├── scrape-app.yml           # vmagent on vl-app: scrapes backend /api/v1/metrics + node-exporter + cadvisor
│   ├── scrape-data.yml          # vmagent on vl-data: scrapes postgres-exporter + node-exporter + cadvisor
│   └── scrape-monitoring.yml    # vmagent on vl-monitoring: scrapes own node-exporter + cadvisor + each VM-stack service
├── vmalert/
│   ├── rules/
│   │   ├── backup.rules.yml          # backup_freshness alert (>26h since last backup)
│   │   ├── container.rules.yml       # container restart-count alert
│   │   ├── clamav.rules.yml          # ClamAV scanner-down alert
│   │   └── deadman.rules.yml         # always-firing Watchdog (heartbeat receiver detects when it stops)
│   └── config.yml                    # placeholder; vmalert is configured via flags in compose
├── alertmanager/
│   └── config.yml                    # routes: default -> Slack webhook; Watchdog -> deadman heartbeat URL
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   ├── victoriametrics.yml   # Prometheus-compatible datasource pointing at VM
│   │   │   └── loki.yml              # Loki datasource
│   │   └── dashboards/
│   │       └── default.yml           # provisioning loader; reads JSON from /var/lib/grafana/dashboards/
│   └── dashboards/
│       └── README.md                 # how to import community dashboards from grafana.com
├── loki/
│   └── config.yml                    # filesystem-backed, gzip on, 30d retention, 256KB per-line cap
└── promtail/
    └── config.yml                    # docker-sd, gzip + batch ship to Loki
```

## Scrape topology

Per-host vmagent pattern: each tier (`vl-edge`, `vl-app`, `vl-data`,
`vl-monitoring`) runs its own vmagent that scrapes targets reachable
on `127.0.0.1` / Docker DNS within that tier, then **remote-writes**
the samples to VictoriaMetrics on `vl-monitoring`.

This is more resilient than centralized scraping for cross-DC
deployments: vmagent buffers samples locally during WG mesh blips and
replays when reachable. With centralized scraping, the same blip
silently loses every sample taken during it.

Remote-write target is parameterized via `VM_REMOTE_WRITE_URL` in
the env profile:

| Profile | `VM_REMOTE_WRITE_URL` |
|---|---|
| `allinone.env` | `http://victoriametrics:8428/api/v1/write` (Docker DNS) |
| `multihost-samedc.env` | `http://vl-monitoring.vuln.lan:8428/api/v1/write` (private network DNS) |
| `multihost-crossdc.env` | `http://vl-monitoring.vuln.lan:8428/api/v1/write` (resolves to WG overlay IP) |

Same shape for `LOKI_PUSH_URL`.

## External labels (service identity)

vmagent attaches `external_labels` to every sample on remote-write,
so VictoriaMetrics can distinguish "metric from backend" from "metric
from caddy" etc. without renaming the metric itself:

```
external_labels:
  service: backend         # set per scrape job
  host: vl-app             # set per vmagent (env var BLOAT_HOST)
  tier: app                # set per vmagent
```

This is why `vl_http_requests_total` doesn't need to become
`vl_backend_http_requests_total` - the service label tells VM which
service emitted it.

## Alert routing

Alertmanager has two routes:

1. **Default** -> `ALERTMANAGER_SLACK_WEBHOOK_URL` from env.
   Empty URL means alerts log internally but don't deliver. Operators
   set this in `.env`.
2. **Watchdog** (always-firing alert from `deadman.rules.yml`) ->
   `ALERTMANAGER_DEADMAN_WEBHOOK_URL` from env. External heartbeat
   receiver (healthchecks.io, Slack heartbeat-bot, cron pinger)
   detects when this STOPS firing - that means Alertmanager itself
   is down or the monitoring tier is unreachable.

Both URLs are operator-provided. The deadman is the safety net for
"who watches the watchman."

## Dashboards

Phase-1 ships with empty dashboards directory. Operators can import
the recommended community dashboards from Grafana's UI on first
login:

| Dashboard | Grafana.com ID | What it shows |
|---|---|---|
| Node Exporter Full | `1860` | Per-host CPU / RAM / disk / network |
| Docker / cAdvisor | `14282` | Per-container resource usage |
| PostgreSQL Database | `9628` | DB activity, locks, slow queries, replication lag |

Custom VulnLedger-business dashboard (the 8 `vl_*_count` gauges from
the backend) lands in a follow-up.

## Image pins

All images tag-pinned in compose. Digest pinning is a follow-up
tracked at [#79](https://github.com/raymond-itsec/vulnledger/issues/79).
