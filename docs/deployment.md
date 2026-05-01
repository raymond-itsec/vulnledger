# Deployment

Three paths, in order of complexity. Pick the one that matches your stage.

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

## Multi-server / distributed

For larger teams or high-availability requirements, services can be split across multiple machines. The standard layout is four hosts:

| Host | Services | Why |
|---|---|---|
| **edge** | caddy, public statuspage | Public attack surface minimized; survives independently |
| **app** | backend, frontend, clamav | Stateless; this is the host you horizontally scale |
| **data** | postgres, seaweedfs, backup | Stateful; disk performance matters most here; co-locating backup with the DB it dumps avoids cross-host streaming |
| **monitoring** | victoriametrics, grafana, alertmanager, loki | Observability separated so workload outages don't blind you |

A WireGuard mesh ties the four hosts together over a private overlay; nothing except Caddy is exposed publicly.

### Per-component quick examples

#### Database server
```bash
docker run -d \
  --name vulnledger-db \
  --restart unless-stopped \
  -e POSTGRES_USER=<db-user> \
  -e POSTGRES_PASSWORD=<strong-password> \
  -e POSTGRES_DB=<db-name> \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine \
  -c shared_buffers=256MB \
  -c work_mem=16MB \
  -c max_connections=100
```

#### Storage server (SeaweedFS)
```bash
docker run -d \
  --name vulnledger-seaweedfs \
  --restart unless-stopped \
  -e AWS_ACCESS_KEY_ID=<access-key> \
  -e AWS_SECRET_ACCESS_KEY=<secret-key> \
  -v seaweedfs_data:/data \
  -p 8333:8333 \
  chrislusf/seaweedfs:4.20 \
  server -dir=/data -s3 -s3.port=8333
```

#### Application server
```bash
# Backend
docker run -d \
  --name vulnledger-backend \
  --restart unless-stopped \
  -e POSTGRES_HOST=<db-host> \
  -e POSTGRES_SERVICE_PORT=5432 \
  -e POSTGRES_USER=<db-user> \
  -e POSTGRES_PASSWORD=<pw> \
  -e POSTGRES_DB=<db-name> \
  -e FINDINGS_OBJECT_STORAGE_ENDPOINT=<seaweedfs-host>:8333 \
  -e FINDINGS_OBJECT_STORAGE_ACCESS_KEY=<key> \
  -e FINDINGS_OBJECT_STORAGE_SECRET_KEY=<secret> \
  -e FINDINGS_JWT_ISSUER=<jwt-issuer> \
  -e FINDINGS_JWT_AUDIENCE=<jwt-audience> \
  -e FINDINGS_JWT_PRIVATE_KEY_FILE=/run/secrets/jwt_private_key.pem \
  -e FINDINGS_JWT_PUBLIC_KEY_FILE=/run/secrets/jwt_public_key.pem \
  -e FINDINGS_CLAMAV_HOST=<clamav-host> \
  -v /host/secrets/jwt_private_key.pem:/run/secrets/jwt_private_key.pem:ro \
  -v /host/secrets/jwt_public_key.pem:/run/secrets/jwt_public_key.pem:ro \
  -p 8000:8000 \
  vulnledger-backend

# Frontend
docker run -d \
  --name vulnledger-frontend \
  --restart unless-stopped \
  -p 5173:5173 \
  vulnledger-frontend
```

#### Reverse proxy (any server with public IP)

Use the Caddyfile with `reverse_proxy` directives pointing to the application server's IP.

#### Backup server
```bash
docker run -d \
  --name vulnledger-backup \
  --restart unless-stopped \
  -e POSTGRES_HOST=<db-host> \
  -e POSTGRES_USER=<db-user> \
  -e POSTGRES_PASSWORD=<pw> \
  -e POSTGRES_DB=<db-name> \
  -e BACKUP_RETENTION_DAYS=90 \
  -e BACKUP_CRON="0 2 * * *" \
  -v /mnt/backup-storage:/backups \
  vulnledger-backup
```

## Allinone vs Multi-host

| | Allinone | Multi-host |
|---|---|---|
| **Hosts** | 1 | 4 (edge / app / data / monitoring) |
| **Networking** | Docker bridges | WireGuard mesh |
| **Failure domain** | One host = entire app | Compromised app host can't reach DB |
| **Scaling** | Vertical only (bigger box) | Horizontal (add another `app` host) |
| **Cost** | One VPS | Four VPSes |
| **When** | Pre-product, internal demos, POCs | Real users, production SLA, security-conscious customers |

Both modes use the same source files. Switching from allinone to multi-host is a matter of provisioning the additional hosts and changing service-discovery hostnames in the env files - not rewriting code or compose definitions.
