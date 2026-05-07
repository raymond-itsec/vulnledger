# Grafana dashboards

This directory is auto-loaded into Grafana by the provisioner at
`../provisioning/dashboards/default.yml`. Drop any `.json` dashboard
file in here and it appears in Grafana within 30 seconds.

## Recommended community dashboards (import on first use)

These work out of the box against the data this stack already
collects. Import via Grafana UI:
**Dashboards → New → Import → Paste ID → Load**.

| ID | Dashboard | What it shows | Source |
|---|---|---|---|
| `1860` | Node Exporter Full | Per-host CPU, RAM, disk, network, uptime | https://grafana.com/grafana/dashboards/1860 |
| `14282` | cAdvisor Containers | Per-container resource usage, restart counts, OOM events | https://grafana.com/grafana/dashboards/14282 |
| `9628` | PostgreSQL Database | DB activity, locks, slow queries, replication lag | https://grafana.com/grafana/dashboards/9628 |

When prompted for a data source during import, pick `VictoriaMetrics`
(provisioned as the default).

## VulnLedger-specific dashboards

A custom dashboard for the 8 `vl_*_count` business gauges plus the
HTTP / DB pool metrics is a follow-up. When that lands, the JSON
will live in this directory and auto-load on next Grafana restart.

## License note on community dashboards

The three IDs above are Apache-2.0 / Public Domain on grafana.com.
Inlining their JSON into the repo is fine; for now we lazy-import
them via the UI to keep the diff focused on the stack bring-up.
