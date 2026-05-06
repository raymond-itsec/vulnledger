# Deployment

VulnLedger ships compose tier files plus a connectivity contract. How you provision the underlying hosts is your choice: bare metal, Proxmox, KVM, ESXi, OVH/Hetzner/Scaleway/Contabo VPSes, or a mix. The application doesn't care.

Three deployment shapes, in order of complexity. Pick the one that matches your stage.

| Shape | Hosts | Networking | When |
|---|---|---|---|
| **Allinone** | 1 | Docker bridges | Pre-product, demos, POCs, internal use |
| **Same-DC multi-host** | 4, same datacenter or rack | Private VLANs (or Docker overlay), optional WireGuard | Real users, single-DC production |
| **Cross-DC multi-host** | 4, geographically distributed | WireGuard mesh as primary connectivity | Geo-redundant production, multi-region |

The **same source files** drive all three. Switching from allinone to multi-host is a matter of provisioning extra hosts, picking a profile env, and pointing service-discovery hostnames at the right places.

## Single-server (Docker Compose)

The recommended approach for most teams.

```bash
# 1. Clone to your server
git clone https://github.com/raymond-itsec/vulnledger.git /opt/vulnledger
cd /opt/vulnledger

# 2. Configure environment
cp .env.example .env
nano .env  # Set production values (see below)

# 3. Set your public host in .env
# CADDY_HOST=yourdomain.com

# 4. Start all services
docker compose up -d

# 5. Verify everything is running
docker compose ps
docker compose logs -f backend  # Watch for startup messages
```

!!! note "Auto-TLS"
    Caddy automatically provisions and renews Let's Encrypt TLS certificates when `CADDY_HOST` is set to a public domain. The default `http://localhost` value keeps local development simple.

The backend container runs `alembic upgrade head` before starting Uvicorn, so normal Docker Compose starts apply pending schema migrations automatically.

### Production environment variables that must change

```env
# CRITICAL - change these!
SEAWEEDFS_S3_ACCESS_KEY=<strong-access-key>
SEAWEEDFS_S3_SECRET_KEY=<strong-secret-key>
FINDINGS_INITIAL_ADMIN_USERNAME=<admin-username>
FINDINGS_INITIAL_ADMIN_PASSWORD=<strong-admin-password>
FINDINGS_INITIAL_ADMIN_EMAIL=<admin-email>
FINDINGS_INITIAL_ADMIN_FULL_NAME=<admin-full-name>
FINDINGS_JWT_ISSUER=<jwt-issuer>
FINDINGS_JWT_AUDIENCE=<jwt-audience>
FINDINGS_JWT_PRIVATE_KEY_FILE=/run/secrets/jwt_private_key.pem
FINDINGS_JWT_PUBLIC_KEY_FILE=/run/secrets/jwt_public_key.pem

# Database (use a strong password)
POSTGRES_USER=change_this_db_user
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DB=change_this_db_name
POSTGRES_HOST=db
POSTGRES_SERVICE_PORT=5432

# Your public URL (used in emails and OIDC redirects)
FINDINGS_APP_BASE_URL=https://yourdomain.com

# Email (Mailjet)
# Register: https://www.mailjet.com/pricing/
FINDINGS_MAILJET_API_KEY=<your-key>
FINDINGS_MAILJET_API_SECRET=<your-secret>
FINDINGS_MAILJET_FROM_EMAIL=security@yourdomain.com
FINDINGS_MAILJET_FROM_NAME=VulnLedger
```

The full list of every environment variable lives in [Configuration](configuration.md).

## Upgrading existing installations

For existing deployments, use the normal pull-and-restart flow:

```bash
git pull
docker compose up -d --build
```

The backend relies on Alembic only and no longer calls `create_all()` on startup. That avoids future collisions where tables created outside Alembic later conflict with versioned migrations.

If you want to run the migration step manually before restarting the full stack:

```bash
docker compose run --rm backend alembic upgrade head
```

If you are upgrading from an older install that previously relied on startup-time table creation, take a database backup first. The current report-export and taxonomy migrations are tolerant of that older bootstrap path, but Alembic should be treated as the source of truth going forward.

## Docker Compose service inventory

The default `docker-compose.yml` runs:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `db` | postgres:16.13-alpine3.23 (digest pinned) | `127.0.0.1:5432` | Primary database |
| `seaweedfs` | chrislusf/seaweedfs:4.20 | `127.0.0.1:8333` | S3-compatible object storage for evidence and generated exports |
| `backend` | Custom (Python 3.12) | `127.0.0.1:8000` | FastAPI REST API |
| `frontend` | Custom (Node 22) | `127.0.0.1:5173` | SvelteKit SPA |
| `caddy` | Custom (Caddy + ratelimit module) | `80`, `443`, `443/udp` | Reverse proxy with optional auto-TLS |
| `backup` | Custom (postgres + cron) | - | Scheduled database backups |
| `clamav` | clamav/clamav:1.4.3 (digest pinned) | `127.0.0.1:3310` | Antivirus scanning |

!!! note
    Most runtime image references in `docker-compose.yml` are pinned by immutable digest. SeaweedFS is pinned to release tag `4.20`; pinning its multi-arch digest is a deployment-hardening follow-up.

### Docker volumes

| Volume | Data | Backup? |
|---|---|---|
| `pgdata` | PostgreSQL data | Auto-backed up by backup service |
| `seaweedfs_data` | Evidence files and generated report exports | Back up separately or use SeaweedFS replication |
| `backups` | SQL dump files (encrypted in production) | Mount to host or NFS for off-server storage |
| `caddy_data` | TLS certificates | Auto-managed by Caddy |
| `clamav_data` | Virus definitions | Auto-updated by ClamAV |

## Multi-host (distributed)

For larger teams, security-conscious deployments, or geo-redundancy, services split across four hosts:

| Host | Tier file | Services | Public IP needed? |
|---|---|---|---|
| **edge** | `deploy/compose/edge.yml` | caddy | Yes (the only public surface) |
| **app** | `deploy/compose/app.yml` | backend, frontend | No |
| **data** | `deploy/compose/data.yml` | postgres, seaweedfs, clamav, backup | No |
| **monitoring** | `deploy/compose/monitoring.yml` | victoriametrics, grafana, alertmanager, loki (planned) | No |

The four hosts can be anything that runs Docker on Linux: bare metal, KVM, Proxmox, ESXi, VPSes from any provider, or a mix.

### Connectivity contract

Whatever you provision, the compose files require this from your network:

| Required reachability | From | To |
|---|---|---|
| postgres on its declared port | app host | data host |
| seaweedfs S3 endpoint | app host | data host |
| clamav | app host | data host |
| backend (HTTP) | edge host | app host |
| frontend (HTTP) | edge host | app host |
| metrics endpoints | monitoring host | every other host |
| public 443 / 80 | internet | edge host |

How you satisfy that is your call. Three common patterns:

**Same-DC, private VLANs**: hosts share a private network at L2/L3. Set `POSTGRES_HOST=vl-data.local` etc. in the multihost env profile, point at private IPs via `/etc/hosts`. No tunneling needed.

**Same-DC, Docker overlay**: a Swarm or Tailscale overlay handles connectivity; tier files unchanged.

**Cross-DC, WireGuard mesh** (recommended for hosts in different datacenters): every host runs a WireGuard interface; all cross-tier traffic rides the encrypted overlay. Public NICs only allow WG (UDP 51820) plus 443 on edge.

### Same-DC quick path (4 VPSes from one provider)

Example using four VPSes from a single European provider (OVH, Hetzner, Scaleway, Contabo, IONOS, etc.) within one datacenter:

```bash
# On each host, after provisioning + Docker install:
git clone https://github.com/raymond-itsec/vulnledger.git /opt/vulnledger
cd /opt/vulnledger

# Set up the WireGuard mesh (or use the provider's private network if available)
# vulnledger ships a key-generation helper at deploy/wireguard/

# Copy the multihost profile
cp deploy/profiles/multihost.env .env

# Edit .env with hostnames pointing at each tier (private IPs or WG overlay IPs)
# POSTGRES_HOST=vl-data.vuln.lan        (resolves via /etc/hosts to data host's IP)
# FINDINGS_OBJECT_STORAGE_ENDPOINT=vl-data.vuln.lan:8333
# FINDINGS_CLAMAV_HOST=vl-data.vuln.lan
# CADDY_BACKEND_UPSTREAM=vl-app.vuln.lan:8000
# CADDY_FRONTEND_UPSTREAM=vl-app.vuln.lan:5173

# Bring up only the tier this host runs:
# On vl-data:
docker compose -f deploy/compose/data.yml up -d
# On vl-app:
docker compose -f deploy/compose/app.yml up -d
# On vl-edge:
docker compose -f deploy/compose/edge.yml up -d
# On vl-monitoring:
docker compose -f deploy/compose/monitoring.yml up -d
```

### Cross-DC quick path (4 VPSes in different datacenters)

Identical to the same-DC flow, except:

1. WireGuard is **mandatory** (no shared private network exists).
2. Every host's public firewall (cloud provider's or nftables) drops everything except WG (UDP 51820), and on `vl-edge` only also 80 + 443.
3. `/etc/hosts` entries point at WireGuard overlay IPs, not provider-private IPs.
4. Each host has its own internet egress; tinyproxy on edge becomes optional rather than architectural.
5. Latency between tiers reflects the inter-DC distance (5-20ms within Europe; more if mixing continents). Some endpoints will feel measurably slower than allinone.

Example operator combinations that work fine:

| Edge | App | Data | Monitoring | Notes |
|---|---|---|---|---|
| OVH (FR) | OVH (FR) | OVH (FR) | OVH (FR) | Same-DC if same region; cross-DC across regions |
| Hetzner (DE) | Hetzner (DE) | Hetzner (DE) | Hetzner (DE) | Same as above |
| OVH (FR) | Hetzner (DE) | Scaleway (FR) | Contabo (DE) | Multi-provider; all cross-DC |
| Bare metal in your rack | Bare metal | Bare metal | Bare metal | Same-DC, no provider |
| Proxmox host (your rack) | Proxmox VM | Proxmox VM | Proxmox VM | Same-DC homelab |
| ESXi host (your rack) | ESXi VM | ESXi VM | ESXi VM | Same-DC homelab; reference recipe in `vulnledger-lab-esxi` |

The application is identical across all of these. Only the network plan changes.

### Reference operator recipe: ESXi + Rocky 10.1

If you want a worked example of provisioning the four hosts from scratch on VMware ESXi free tier with Packer + ovftool + Rocky Linux 10.1, see the optional companion repo `vulnledger-lab-esxi` (Packer template, cloud-init, nftables rulesets, ovftool deploy script).

That repo is one possible operator path, not a prerequisite. Most operators will already have their own provisioning tooling (Terraform, Ansible, cloud-init via their provider's API, etc.) and just need the connectivity contract above.
