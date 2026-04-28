# VulnLedger

VulnLedger is a self-hosted web application for managing security code review findings. Built for security consultants and teams who need to track clients, reviewed assets, code review sessions, and individual findings -- with full edit history, report generation, and email notifications.

**Fully self-hostable. No US Cloud Act dependencies. Your data stays yours.**

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Local Development Setup](#local-development-setup)
- [Production / Distributed Deployment](#production--distributed-deployment)
- [Configuration Reference](#configuration-reference)
- [Finding Templates](#finding-templates)
- [API Overview](#api-overview)
- [Security](#security)
- [Backup & Recovery](#backup--recovery)

---

## Features

### Core
- **Client Management** -- Track clients with contact details and linked assets
- **Asset Tracking** -- Catalog reviewed assets (web apps, APIs, mobile apps, infrastructure, etc.)
- **Review Sessions** -- Organize findings per engagement with reviewer assignment and status tracking
- **Finding Management** -- Full CRUD with risk levels (critical → informational), remediation statuses, markdown-rich descriptions, and file attachments
- **Change History** -- Per-field audit trail on every finding edit (who changed what, when)
- **File Attachments** -- Upload screenshots, evidence, and documents (stored in SeaweedFS S3-compatible object storage)

### Templates
- **25 Built-in Finding Templates** -- Covering OWASP Top 10 categories: injection, authentication, access control, cryptography, misconfiguration, and more
- **Custom Templates** -- Create, edit, and delete your own finding templates
- **YAML-based Sync** -- Built-in templates managed via YAML files, idempotent sync on startup

### Reporting & Notifications
- **PDF Reports** -- Professional, styled security review reports with executive summary, risk breakdown, and detailed findings (WeasyPrint)
- **CSV Export** -- Spreadsheet-friendly export of all findings per session
- **JSON Export** -- Structured data export for integration with other tools
- **Stored Export History** -- Generated PDF/CSV/JSON exports are recorded per session with export date, file name, creator, and later download access
- **Email Notifications** -- Via Mailjet: new finding alerts, status change notifications, report-ready notifications

### Dashboard
- **Risk Level Breakdown** -- Visual bar charts of findings by severity
- **Status Breakdown** -- At-a-glance remediation progress
- **Quick Actions** -- One-click access to create clients, findings
- **Recent Activity** -- Latest sessions and findings

### Security & Operations
- **JWT Authentication** -- Access tokens (5 min) + HttpOnly refresh token cookies (7 days)
- **Role-Based Access Control** -- Admin, Reviewer, Client User roles with data isolation
- **Versioned Taxonomies** -- DB-managed risk, remediation, session-status, and asset-type taxonomies with explicit active versions
- **Availability Banner** -- Shared top-of-page outage notice for backend, proxy, database-startup, or local network failures that should not be treated as normal per-request UI errors
- **Rate Limiting** -- Brute-force protection on login, configurable API limits
- **Security Headers** -- CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Optional OIDC SSO** -- Integrate with any OpenID Connect provider (Keycloak, Azure AD, Okta, etc.)
- **Virus Scanning** -- ClamAV integration scans every file upload before storage and blocks uploads if the scanner is configured but unavailable
- **Automated Backups** -- Scheduled PostgreSQL dumps with configurable retention

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12, FastAPI | REST API, async request handling |
| **ORM** | SQLAlchemy 2.0 (async) | Database models and queries |
| **Database** | PostgreSQL 16 | Primary data store |
| **Migrations** | Alembic | Database schema versioning |
| **Frontend** | SvelteKit 5, TypeScript | Single-page application |
| **Styling** | Custom CSS (CSS variables) | Theming, responsive design |
| **Object Storage** | SeaweedFS | S3-compatible file attachment and report export storage |
| **Reverse Proxy** | Caddy 2 | Auto-TLS, routing, compression |
| **PDF Generation** | WeasyPrint | HTML → PDF report rendering |
| **Email** | Mailjet (REST API) | Transactional email notifications |
| **Auth** | python-jose (JWT), bcrypt | Token-based auth, password hashing |
| **SSO** | Authlib | Optional OIDC/OpenID Connect |
| **Antivirus** | ClamAV + clamd | Attachment virus scanning |
| **Rate Limiting** | slowapi | Request throttling |
| **Markdown** | mistune | Server-side markdown rendering for PDF |
| **Containerization** | Docker, Docker Compose | Deployment and orchestration |

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│   Browser    │────│    Caddy     │────│   Frontend   │
│              │     │  (reverse    │     │  (SvelteKit) │
│              │     │   proxy)     │     │  :5173       │
└──────────────┘     │  :80/:443   │     └──────────────┘
                     │              │
                     │              │     ┌──────────────┐
                     │   /api/*  ───│────│   Backend    │
                     │              │     │  (FastAPI)   │
                     └──────────────┘     │  :8000       │
                                          │              │
                           ┌──────────────┤              ├──────────────┐
                           │              │              │              │
                           ▼              └──────┬───────┘              ▼
                     ┌──────────┐                │                ┌──────────┐
                     │ PostgreSQL│                │                │SeaweedFS │
                     │  :5432   │                │                │  :8333   │
                     └──────────┘                │                └──────────┘
                           ▲                     │
                           │                     ▼
                     ┌──────────┐          ┌──────────┐
                     │  Backup  │          │  ClamAV  │
                     │ (cron)   │          │  :3310   │
                     └──────────┘          └──────────┘
```

### Request Flow
1. All requests enter through **Caddy** (ports 80/443)
2. Requests to `/api/*` are proxied to the **FastAPI backend**
3. All other requests are proxied to the **SvelteKit frontend**
4. The backend communicates with **PostgreSQL** for data, **SeaweedFS** for files, **ClamAV** for scanning, and **Mailjet** for email
5. The **backup service** independently dumps PostgreSQL on a cron schedule

### Storage Layout
- **Evidence bucket** -- Uploaded finding attachments are stored in the configured object-storage evidence bucket
- **Reports bucket** -- Generated PDF, CSV, and JSON exports are stored in a separate object-storage reports bucket
- **Report retention** -- Newly generated reports are uploaded with one-year object-lock retention and recorded with SHA256 integrity metadata
- **Stored export downloads** -- Session detail pages can list and download previously generated exports through the backend

### v0.2.0 Breaking Storage Change
VulnLedger `v0.2.0` starts object storage from SeaweedFS. The default deployment no longer starts MinIO and does not automatically migrate old MinIO buckets or objects. Fresh deployments only need the SeaweedFS settings in `.env`; existing deployments must either accept a fresh object store or manually copy existing MinIO objects into SeaweedFS before old attachment/report downloads are expected to work.

### Authentication Flow
1. User submits credentials → `POST /api/auth/login`
2. Backend verifies with bcrypt, returns JWT access token + sets HttpOnly refresh cookie
3. Frontend stores access token in memory (not localStorage -- XSS safe)
4. On page load or after a 401, the frontend calls `POST /api/auth/refresh` using the cookie
5. Refresh rotates both tokens transparently and restores the in-memory access token from DB-backed refresh session state
6. All non-login frontend pages require authentication and redirect back to `/` when the user is signed out
7. Logout clears the refresh cookie, drops the in-memory access token, and returns the browser to the login page
8. Backend/container restarts do not invalidate active refresh-session families; users sign in again only after logout, expiry, or detected token reuse
9. Signed-in sessions poll the authenticated health endpoint to drive the shared availability banner, while the login page performs only a one-time startup availability probe per browser tab session

### OIDC SSO Flow (Optional)
1. User clicks "Sign in with SSO" → `GET /api/auth/oidc/login`
2. Redirect to Identity Provider (IdP)
3. IdP callback → `GET /api/auth/oidc/callback`
4. Backend auto-provisions user from OIDC claims if new
5. Redirect to the frontend, which restores the session from the refresh cookie

---

## Data Model

```
Users ──────────────────────────────────────┐
  │                                         │
  │ reviewer_id                             │ linked_client_id
  ▼                                         ▼
ReviewSessions ── asset_id ── ReviewedAssets ── client_id ── Clients
  │                                                              │
  │ session_id                                                   │
  ▼                                                              │
Findings ── FindingHistory (per-field change log)               │
  │                                                              │
  │ finding_id                                      Users.linked_client_id
  ▼                                    (client_user sees only their client's data)
FindingAttachments (object storage)

ReviewSessions ── ReportExports (stored export metadata + object key + taxonomy version)

TaxonomyVersions ── TaxonomyEntries
       ▲
       └──── active version drives risk/status/asset validation, labels, colors, and export rendering

FindingTemplates (25 built-in + custom)
```

### Taxonomy Model

VulnLedger uses DB-managed versioned taxonomies for:
- `risk_level`
- `remediation_status`
- `session_status`
- `asset_type`

Each taxonomy entry stores a machine value plus its label, sort order, optional color, and active state. The active taxonomy version drives live backend validation and frontend UI options. Stored exports also record the taxonomy version that was active when the artifact was generated.

### Roles
| Role | Permissions |
|------|------------|
| **admin** | Full access. Manage users, edit built-in templates, all data |
| **reviewer** | Create/edit clients, assets, sessions, findings, templates. Cannot manage users |
| **client_user** | Read-only access scoped to their linked client's data only |

---

## Local Development Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) v2+
- [Node.js](https://nodejs.org/) 22+ (for frontend development)
- [Python](https://www.python.org/) 3.12+ (for backend development)

### Quick Start (Docker -- recommended)

```bash
# 1. Clone the repository
git clone https://github.com/raymond-itsec/vulnledger.git vulnledger
cd vulnledger

# 2. Create your local environment file
./scripts/first-run.sh init

# 3. Review the secrets and initial admin values in .env
# Optional: configure Mailjet if you want email notifications
# Register: https://www.mailjet.com/pricing/
# Quick start: https://documentation.mailjet.com/hc/en-us/articles/37251169295003--Quick-Start-with-Mailjet

# 4. Run the preflight checks
./scripts/first-run.sh doctor

# 5. Start all services
./scripts/first-run.sh up

# 6. Open in browser
open http://localhost
```

That's it. The app will be available at `http://localhost` with:
- Your configured initial admin account from `.env`
- 25 finding templates auto-synced on startup
- PostgreSQL, SeaweedFS, and all services running

### First-Run Helper

The VulnLedger repository includes a helper script for smoother installs:

```bash
./scripts/first-run.sh init    # create .env from .env.example
./scripts/first-run.sh doctor  # validate ports, secrets, and common setup issues
./scripts/first-run.sh redeploy  # ff-only pull + ordered rollout: migrate DB, backend, frontend
./scripts/first-run.sh verify-backend  # local Python 3.12 backend smoke-check
PYTHONPATH=backend FINDINGS_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" python backend/scripts/export_openapi.py backend/openapi.generated.json
npm --prefix frontend run generate:types  # regenerate frontend API types from backend OpenAPI
./scripts/first-run.sh up      # ordered rollout (same as redeploy)
./scripts/first-run.sh logs    # follow caddy, frontend, and backend logs
./scripts/first-run.sh down    # stop the stack
./scripts/first-run.sh reset   # stop the stack and remove named volumes
```

`doctor` catches two common setup problems before Docker starts:
- Host ports that are already in use
- Placeholder secrets that were never updated in `.env`

`scripts/first-run.sh` always uses production containers from `docker-compose.yml`. The backend image build context is `./backend`.

`redeploy` now starts with `git pull --ff-only` (and exits if tracked git changes are present), then enforces rollout order. It runs DB migrations first. It deploys backend second. It waits for backend readiness. It deploys frontend and Caddy last.

`reset` is the safest retry path after a failed first install if you changed `POSTGRES_PASSWORD`, because PostgreSQL only applies that password when initializing a fresh data directory.

### Local Development (optional)

If you want to develop with live reloading on both frontend and backend:

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies (WeasyPrint needs system libs -- see below)
pip install -r requirements.lock.txt

# If requirements.txt changed, refresh the lock file
./scripts/lock-requirements.sh

# Start PostgreSQL (if not using Docker)
# Ensure POSTGRES_HOST and POSTGRES_SERVICE_PORT point to your local PostgreSQL

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

The backend no longer auto-creates tables on startup. Alembic is the canonical schema manager for both local development and deployed environments.

>  **WeasyPrint system dependencies** (required for PDF generation):
> - **macOS:** `brew install pango libffi cairo glib`
> - **Ubuntu/Debian:** `apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2`
> - **Docker:** Already handled in the Dockerfile

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies `/api/*` to the backend.

#### Supporting Services

You can run just the infrastructure services via Docker while developing locally:

```bash
# Start only PostgreSQL and SeaweedFS
docker compose up -d db seaweedfs

# Optional: Start ClamAV for virus scanning
docker compose up -d clamav
```

### Environment Variables

Create a `.env` file in the project root (or set environment variables):

```env
# Required
POSTGRES_USER=change_this_db_user
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DB=change_this_db_name
POSTGRES_HOST=localhost
POSTGRES_SERVICE_PORT=5432
FINDINGS_SECRET_KEY=change-this-jwt-signing-key
FINDINGS_INITIAL_ADMIN_USERNAME=admin
FINDINGS_INITIAL_ADMIN_PASSWORD=change-this-admin-password
FINDINGS_INITIAL_ADMIN_EMAIL=admin@example.com

# SeaweedFS S3-compatible object storage
FINDINGS_OBJECT_STORAGE_ENDPOINT=localhost:8333
FINDINGS_OBJECT_STORAGE_ACCESS_KEY=findings-storage
FINDINGS_OBJECT_STORAGE_SECRET_KEY=change-this-object-storage-secret
FINDINGS_OBJECT_STORAGE_SECURE=false
FINDINGS_OBJECT_STORAGE_EVIDENCE_BUCKET=finding-attachments
FINDINGS_OBJECT_STORAGE_REPORTS_BUCKET=generated-reports
FINDINGS_REPORT_RETENTION_DAYS=365

# Optional: Upload / report guardrails
# The backend value is the authoritative attachment limit.
# Keep the Caddy limit at or slightly above it so oversized uploads are rejected early.
FINDINGS_ATTACHMENT_MAX_FILE_SIZE_MB=25
FINDINGS_REPORT_MAX_FINDINGS=250
FINDINGS_REPORT_MAX_INPUT_CHARS=200000
FINDINGS_REPORT_MAX_OUTPUT_SIZE_MB=25

# Optional: Email notifications
# Register: https://www.mailjet.com/pricing/
# Quick start: https://documentation.mailjet.com/hc/en-us/articles/37251169295003--Quick-Start-with-Mailjet
FINDINGS_MAILJET_API_KEY=your-mailjet-key
FINDINGS_MAILJET_API_SECRET=your-mailjet-secret
FINDINGS_MAILJET_FROM_EMAIL=security@yourcompany.com
FINDINGS_MAILJET_FROM_NAME=VulnLedger
FINDINGS_APP_BASE_URL=http://localhost

# Optional: OIDC SSO
FINDINGS_OIDC_ENABLED=false
FINDINGS_OIDC_CLIENT_ID=
FINDINGS_OIDC_CLIENT_SECRET=
FINDINGS_OIDC_DISCOVERY_URL=
FINDINGS_OIDC_REDIRECT_URI=

# JWT / session identity
FINDINGS_JWT_ISSUER=vulnledger-backend
FINDINGS_JWT_AUDIENCE=vulnledger-api
FINDINGS_SESSION_HINT_COOKIE_NAME=vl_session

# Optional: ClamAV
FINDINGS_CLAMAV_HOST=localhost
FINDINGS_CLAMAV_PORT=3310

# Optional: Reverse proxy upload cap (Caddy)
CADDY_ATTACHMENT_MAX_SIZE=30MB

# Optional: Unified app version shown in UI and backend metadata
APP_VERSION=0.2.0
```

---

## Production / Distributed Deployment

### Single-Server Deployment (Docker Compose)

This is the recommended approach for most teams.

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

>  Caddy automatically provisions and renews Let's Encrypt TLS certificates when `CADDY_HOST` is set to a public domain. The default `http://localhost` value keeps local development simple.

The backend container runs `alembic upgrade head` before starting Uvicorn, so normal Docker Compose starts apply pending schema migrations automatically.

### Upgrading Existing Installations

For existing deployments, use the normal pull-and-restart flow:

```bash
git pull
docker compose up -d --build
```

The backend now relies on Alembic only and no longer calls `create_all()` on startup. That avoids future collisions where tables created outside Alembic later conflict with versioned migrations.

If you want to run the migration step manually before restarting the full stack, use:

```bash
docker compose run --rm backend alembic upgrade head
```

If you are upgrading from an older install that previously relied on startup-time table creation, take a database backup first. The current report-export and taxonomy migrations are tolerant of that older bootstrap path, but Alembic should be treated as the source of truth going forward.

### Production Environment Variables

These **must** be changed from defaults:

```env
# CRITICAL -- change these!
FINDINGS_SECRET_KEY=<random-64-char-string>
SEAWEEDFS_S3_ACCESS_KEY=<strong-access-key>
SEAWEEDFS_S3_SECRET_KEY=<strong-secret-key>
FINDINGS_INITIAL_ADMIN_USERNAME=<admin-username>
FINDINGS_INITIAL_ADMIN_PASSWORD=<strong-admin-password>
FINDINGS_INITIAL_ADMIN_EMAIL=<admin-email>

# Database (use strong password)
POSTGRES_USER=change_this_db_user
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DB=change_this_db_name
POSTGRES_HOST=db
POSTGRES_SERVICE_PORT=5432

# Your public URL (used in emails and OIDC redirects)
FINDINGS_APP_BASE_URL=https://yourdomain.com

# Email (Mailjet)
# Register: https://www.mailjet.com/pricing/
# Quick start: https://documentation.mailjet.com/hc/en-us/articles/37251169295003--Quick-Start-with-Mailjet
FINDINGS_MAILJET_API_KEY=<your-key>
FINDINGS_MAILJET_API_SECRET=<your-secret>
FINDINGS_MAILJET_FROM_EMAIL=security@yourdomain.com
FINDINGS_MAILJET_FROM_NAME=VulnLedger
```

### Multi-Server / Distributed Deployment

For larger teams or high-availability requirements, you can split services across multiple machines.

#### Database Server
```bash
# Run PostgreSQL separately with proper tuning
docker run -d \
  --name findings-db \
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

#### Storage Server (SeaweedFS)
```bash
# Run SeaweedFS with its S3 gateway enabled
docker run -d \
  --name findings-seaweedfs \
  --restart unless-stopped \
  -e AWS_ACCESS_KEY_ID=<access-key> \
  -e AWS_SECRET_ACCESS_KEY=<secret-key> \
  -v seaweedfs_data:/data \
  -p 8333:8333 \
  chrislusf/seaweedfs:4.20 \
  server -dir=/data -s3 -s3.port=8333
```

#### Application Server
```bash
# Backend
docker run -d \
  --name findings-backend \
  --restart unless-stopped \
  -e POSTGRES_HOST=<db-host> \
  -e POSTGRES_SERVICE_PORT=5432 \
  -e POSTGRES_USER=<db-user> \
  -e POSTGRES_PASSWORD=<pw> \
  -e POSTGRES_DB=<db-name> \
  -e FINDINGS_SECRET_KEY=<secret> \
  -e FINDINGS_OBJECT_STORAGE_ENDPOINT=<seaweedfs-host>:8333 \
  -e FINDINGS_OBJECT_STORAGE_ACCESS_KEY=<key> \
  -e FINDINGS_OBJECT_STORAGE_SECRET_KEY=<secret> \
  -e FINDINGS_CLAMAV_HOST=<clamav-host> \
  -p 8000:8000 \
  findings-backend

# Frontend
docker run -d \
  --name findings-frontend \
  --restart unless-stopped \
  -p 5173:5173 \
  findings-frontend
```

#### Reverse Proxy (any server with public IP)

Use the Caddyfile with `reverse_proxy` pointing to the application server's IP.

#### Backup Server
```bash
docker run -d \
  --name findings-backup \
  --restart unless-stopped \
  -e POSTGRES_HOST=<db-host> \
  -e POSTGRES_USER=<db-user> \
  -e POSTGRES_PASSWORD=<pw> \
  -e POSTGRES_DB=<db-name> \
  -e BACKUP_RETENTION_DAYS=90 \
  -e BACKUP_CRON="0 2 * * *" \
  -v /mnt/backup-storage:/backups \
  findings-backup
```

### Docker Compose (Production) -- All Services

The default `docker-compose.yml` runs all 7 services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `db` | postgres:16.13-alpine3.23@sha256:... | `127.0.0.1:5432` | Primary database |
| `seaweedfs` | chrislusf/seaweedfs:4.20 | `127.0.0.1:8333` | S3-compatible object storage for evidence and generated exports |
| `backend` | Custom (Python 3.12) | `127.0.0.1:8000` | FastAPI REST API |
| `frontend` | Custom (Node 22) | `127.0.0.1:5173` | SvelteKit SPA |
| `caddy` | Custom (Caddy + ratelimit module) | `80`, `443`, `443/udp` | Reverse proxy with optional auto-TLS |
| `backup` | Custom (postgres + cron) | -- | Scheduled database backups |
| `clamav` | clamav/clamav:1.4.3@sha256:... | `127.0.0.1:3310` | Antivirus scanning |

> Most runtime image references in `docker-compose.yml` are pinned by immutable digest. SeaweedFS is pinned to release tag `4.20`; pinning its multi-arch digest is a deployment hardening follow-up.

### Volumes

| Volume | Data | Backup? |
|--------|------|---------|
| `pgdata` | PostgreSQL data |  Auto-backed up by backup service |
| `seaweedfs_data` | Evidence files and generated report exports |  Back up separately or use SeaweedFS replication |
| `backups` | SQL dump files |  Mount to host or NFS for off-server storage |
| `caddy_data` | TLS certificates |  Auto-managed by Caddy |
| `clamav_data` | Virus definitions |  Auto-updated by ClamAV |

---

## Configuration Reference

Application settings use the `FINDINGS_` prefix. The deployment also exposes supporting Docker, port, and Caddy variables through the same `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | See `.env.example` | PostgreSQL host used by the backend to build its connection string |
| `POSTGRES_SERVICE_PORT` | See `.env.example` | PostgreSQL container/service port used by the backend connection string |
| `POSTGRES_USER` | See `.env.example` | PostgreSQL username |
| `POSTGRES_PASSWORD` | See `.env.example` | PostgreSQL password |
| `POSTGRES_DB` | See `.env.example` | PostgreSQL database name |
| `FINDINGS_SECRET_KEY` | _(empty)_ | JWT signing key (required). Must be at least 32 bytes; the backend logs a CRITICAL message and refuses to start otherwise. |
| `FINDINGS_LOG_LEVEL` | `INFO` | Backend log verbosity (`DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL`, case-insensitive). Invalid values refuse startup. |
| `FINDINGS_ACCESS_TOKEN_EXPIRE_MINUTES` | `5` | Access token lifetime |
| `FINDINGS_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Per-token refresh lifetime; each rotation issues a new token with this expiry (bounded by the family cap below) |
| `FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS` | `30` | **Security policy.** Absolute ceiling on a single login — no amount of rotation extends a refresh-token family past this. When crossed, the family is revoked and the user must log in again. Must be between `7` and `30` inclusive. |
| `FINDINGS_REFRESH_SESSION_RETENTION_DAYS` | _auto_ (`2 x FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS`) | **DB housekeeping.** How long already-dead refresh-session rows (expired or revoked) are kept in `auth_refresh_sessions` before the pruner deletes them. Must be `>= 2 x FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS`. Affects forensic/audit window only; has no effect on auth behavior. |
| `FINDINGS_TRUST_PROXY_HEADERS` | `false` | Trust proxy headers (for example from Caddy) to extract real client IPs |
| `FINDINGS_ALLOWED_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | CORS allowed origins |
| `FINDINGS_ALLOWED_METHODS` | `["GET","POST","PATCH","DELETE","OPTIONS"]` | CORS allowed methods |
| `FINDINGS_ALLOWED_HEADERS` | `["Authorization","Content-Type","Accept","If-None-Match"]` | CORS allowed request headers |
| `FINDINGS_OBJECT_STORAGE_ENDPOINT` | `seaweedfs:8333` | S3-compatible object-storage endpoint |
| `FINDINGS_OBJECT_STORAGE_ACCESS_KEY` | _(empty)_ | Object-storage access key |
| `FINDINGS_OBJECT_STORAGE_SECRET_KEY` | _(empty)_ | Object-storage secret key |
| `FINDINGS_OBJECT_STORAGE_SECURE` | `false` | Use HTTPS for object storage |
| `FINDINGS_OBJECT_STORAGE_EVIDENCE_BUCKET` | `finding-attachments` | Bucket for uploaded finding evidence |
| `FINDINGS_OBJECT_STORAGE_REPORTS_BUCKET` | `generated-reports` | Bucket for generated PDF/CSV/JSON exports |
| `FINDINGS_ATTACHMENT_MAX_FILE_SIZE_MB` | `25` | Authoritative attachment size limit enforced by the backend |
| `FINDINGS_REPORT_MAX_FINDINGS` | `250` | Maximum number of findings allowed in a single export |
| `FINDINGS_REPORT_MAX_INPUT_CHARS` | `200000` | Maximum combined text size allowed before report generation |
| `FINDINGS_REPORT_MAX_OUTPUT_SIZE_MB` | `25` | Maximum generated report size before the backend rejects the export |
| `FINDINGS_REPORT_RETENTION_DAYS` | `365` | Object-lock retention window applied to newly generated stored reports |
| `FINDINGS_MAILJET_API_KEY` | _(empty)_ | Mailjet API key (empty = emails disabled) |
| `FINDINGS_MAILJET_API_SECRET` | _(empty)_ | Mailjet API secret |
| `FINDINGS_MAILJET_FROM_EMAIL` | `noreply@findings.local` | Sender email address |
| `FINDINGS_MAILJET_FROM_NAME` | `VulnLedger` | Sender display name |
| `FINDINGS_APP_BASE_URL` | `http://localhost` | Public URL (used in emails and redirects) |
| `FINDINGS_RATE_LIMIT_LOGIN` | `5/minute` | Login endpoint rate limit |
| `FINDINGS_RATE_LIMIT_API` | `60/minute` | Default API rate limit |
| `FINDINGS_OIDC_ENABLED` | `false` | Enable OIDC SSO |
| `FINDINGS_OIDC_CLIENT_ID` | _(empty)_ | OIDC client ID |
| `FINDINGS_OIDC_CLIENT_SECRET` | _(empty)_ | OIDC client secret |
| `FINDINGS_OIDC_DISCOVERY_URL` | _(empty)_ | OIDC discovery URL (`.well-known/openid-configuration`) |
| `FINDINGS_OIDC_REDIRECT_URI` | _(empty)_ | OIDC callback URL |
| `FINDINGS_OIDC_REDIRECT_URI_ALLOWLIST` | `[]` | Explicit allowlist for OIDC callback redirect URI |
| `FINDINGS_OIDC_REQUIRE_NONCE` | `true` | Require nonce validation on OIDC callback |
| `FINDINGS_OIDC_DEFAULT_ROLE` | `reviewer` | Default role for auto-provisioned SSO users |
| `FINDINGS_INITIAL_ADMIN_USERNAME` | _(empty)_ | Username for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_PASSWORD` | _(empty)_ | Password for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_EMAIL` | _(empty)_ | Email for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_FULL_NAME` | `Administrator` | Display name for the one-time seeded admin account |
| `FINDINGS_CLAMAV_HOST` | _(empty)_ | ClamAV host (empty = scanning disabled) |
| `FINDINGS_CLAMAV_PORT` | `3310` | ClamAV TCP port |
| `FINDINGS_JWT_PRIMARY_ALGORITHM` | `HS256` | Access-token signing algorithm (`HS256` or `RS256`) |
| `FINDINGS_JWT_ALLOW_LEGACY_HS256` | `true` | When enabled, token verification still accepts HS256 during RS256 migration |
| `FINDINGS_JWT_ISSUER` | See `.env.example` | Expected JWT issuer claim |
| `FINDINGS_JWT_AUDIENCE` | See `.env.example` | Expected JWT audience claim |
| `FINDINGS_JWT_PRIVATE_KEY_PEM` | _(empty)_ | RS256 private key PEM (required when RS256 signing is enabled) |
| `FINDINGS_JWT_PUBLIC_KEY_PEM` | _(empty)_ | RS256 public key PEM |
| `FINDINGS_JWT_PRIVATE_KEY_FILE` | See `.env.example` | Path to an RS256 private key PEM file mounted in the backend container |
| `FINDINGS_JWT_PUBLIC_KEY_FILE` | See `.env.example` | Path to an RS256 public key PEM file mounted in the backend container |
| `FINDINGS_SESSION_HINT_COOKIE_NAME` | See `.env.example` | Non-sensitive session-hint cookie name used for OIDC/logout cleanup |
| `FINDINGS_RUNTIME_MODE` | `development` | Runtime mode used by backup encryption policy (`production` enforces secret presence) |
| `APP_VERSION` | `0.2.0` | Shared deployment version for frontend display (`VITE_APP_VERSION`) and backend metadata (`FINDINGS_APP_VERSION`) |
| `POSTGRES_PORT` | `5432` | Host port published for PostgreSQL |
| `SEAWEEDFS_S3_PORT` | `8333` | Host port published for the SeaweedFS S3 gateway |
| `BACKEND_PORT` | `8000` | Host port published for the FastAPI backend |
| `FRONTEND_PORT` | `5173` | Host port published for the Svelte frontend |
| `CLAMAV_PORT` | `3310` | Host port published for ClamAV |
| `CADDY_HTTP_PORT` | `80` | Host port published for Caddy HTTP |
| `CADDY_HTTPS_PORT` | `443` | Host port published for Caddy HTTPS and HTTP/3 |
| `CADDY_ATTACHMENT_MAX_SIZE` | `30MB` | Reverse-proxy upload body limit; keep this at or slightly above `FINDINGS_ATTACHMENT_MAX_FILE_SIZE_MB` |
| `GATUS_PORT` | `8080` | Host port published for the optional Gatus monitoring dashboard (only when started with `--profile monitoring`) |

### Migrating JWT signing from HS256 to RS256

Access tokens are signed with `HS256` by default (shared-secret `FINDINGS_SECRET_KEY`). To rotate to asymmetric `RS256` without logging every user out, follow these steps in order:

1. **Generate an RS256 key pair** (keep the private key secret; 2048-bit RSA minimum):
   ```bash
   openssl genrsa -out jwt-private.pem 2048
   openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem
   ```
2. **Load both keys and enable dual-verify** -- deploy with these env vars. The backend keeps accepting old HS256 tokens while issuing new RS256 tokens:
   ```bash
   FINDINGS_JWT_PRIVATE_KEY_PEM="$(cat jwt-private.pem)"
   FINDINGS_JWT_PUBLIC_KEY_PEM="$(cat jwt-public.pem)"
   FINDINGS_JWT_PRIMARY_ALGORITHM=RS256
   FINDINGS_JWT_ALLOW_LEGACY_HS256=true   # keep HS256 verify on during cutover
   ```
3. **Wait out the access-token TTL** -- all HS256 tokens issued before the switch expire within `FINDINGS_ACCESS_TOKEN_EXPIRE_MINUTES` (default 5 min). Refresh cookies continue to work; users silently receive RS256 tokens on the next refresh.
4. **Disable HS256 verification** -- once the TTL has elapsed (err on the side of 2x):
   ```bash
   FINDINGS_JWT_ALLOW_LEGACY_HS256=false
   ```
   Redeploy. The backend will now reject any remaining HS256 tokens. The HS256 secret can be rotated or removed on a later deploy.

Do not skip step 3: flipping `FINDINGS_JWT_ALLOW_LEGACY_HS256=false` immediately after step 2 invalidates every outstanding access token and forces all users to refresh.

### Backup Configuration

Set on the `backup` service (not `FINDINGS_` prefix):

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_CRON` | `0 2 * * *` | Cron schedule (default: daily 2 AM) |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep old backups |
| `BACKUP_ENCRYPTION_SECRET_FILE` | `/run/secrets/backup_encryption_passphrase` | Path to backup encryption passphrase file |
| `BACKUP_ENCRYPTION_REQUIRED` | `false` | Require passphrase file for every backup; forced in `production` runtime mode |

---

## Finding Templates

The application ships with **25 built-in finding templates** organized by category:

| Category | Templates |
|----------|-----------|
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

### Custom Templates
Create custom templates through the UI (Templates → New Template) or add YAML files to `backend/templates/custom/`.

---

## API Overview

All endpoints are prefixed with `/api`. Authentication is via Bearer token in the `Authorization` header. The only public routes are the login/logout/refresh endpoints and the optional OIDC entry/callback endpoints. All other API routes require an authenticated session.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/login` | Login, get access token | Public |
| `POST` | `/api/auth/refresh` | Refresh access token | Cookie |
| `POST` | `/api/auth/logout` | Clear refresh cookie | Public |
| `GET` | `/api/auth/oidc/login` | Start OIDC flow | Public |
| `GET` | `/api/auth/oidc/callback` | OIDC callback | Public |
| | | | |
| `GET` | `/api/users` | List users | Admin |
| `GET` | `/api/users/reviewers` | List active reviewers | Admin/Reviewer |
| `GET` | `/api/users/me` | Current user profile | Authenticated |
| `POST` | `/api/users` | Create user | Admin |
| | | | |
| `GET` | `/api/clients` | List clients | Authenticated |
| `POST` | `/api/clients` | Create client | Admin/Reviewer |
| `GET` | `/api/clients/:id` | Get client | Authenticated |
| `PATCH` | `/api/clients/:id` | Update client | Admin/Reviewer |
| | | | |
| `GET` | `/api/assets` | List assets | Authenticated |
| `POST` | `/api/assets` | Create asset | Admin/Reviewer |
| `GET` | `/api/assets/:id` | Get asset | Authenticated |
| `PATCH` | `/api/assets/:id` | Update asset | Admin/Reviewer |
| | | | |
| `GET` | `/api/sessions` | List sessions | Authenticated |
| `POST` | `/api/sessions` | Create session | Admin/Reviewer |
| `GET` | `/api/sessions/:id` | Get session | Authenticated |
| `PATCH` | `/api/sessions/:id` | Update session | Admin/Reviewer |
| | | | |
| `GET` | `/api/findings` | List findings (filterable) | Authenticated |
| `POST` | `/api/findings` | Create finding | Admin/Reviewer |
| `GET` | `/api/findings/:id` | Get finding | Authenticated |
| `PATCH` | `/api/findings/:id` | Update finding | Admin/Reviewer |
| `GET` | `/api/findings/:id/history` | Get change history | Authenticated |
| | | | |
| `GET` | `/api/findings/:id/attachments` | List attachments | Authenticated |
| `POST` | `/api/findings/:id/attachments` | Upload file | Admin/Reviewer |
| `GET` | `/api/attachments/:id/download` | Download file | Authenticated |
| `DELETE` | `/api/attachments/:id` | Delete file | Admin/Reviewer |
| | | | |
| `GET` | `/api/templates` | List templates | Authenticated |
| `POST` | `/api/templates` | Create template | Admin/Reviewer |
| `GET` | `/api/templates/:id` | Get template | Authenticated |
| `PATCH` | `/api/templates/:id` | Update template | Admin/Reviewer |
| `DELETE` | `/api/templates/:id` | Delete template | Admin/Reviewer |
| | | | |
| `GET` | `/api/taxonomy/current` | Get the active taxonomy version | Authenticated |
| `GET` | `/api/taxonomy/versions` | List all taxonomy versions | Admin |
| `POST` | `/api/taxonomy/versions` | Create and activate a new taxonomy version | Admin |
| `POST` | `/api/taxonomy/activate` | Activate an existing taxonomy version | Admin |
| | | | |
| `GET` | `/api/reports/sessions/:id/pdf` | Download PDF report | Authenticated |
| `GET` | `/api/reports/sessions/:id/csv` | Download CSV export | Authenticated |
| `GET` | `/api/reports/sessions/:id/json` | Download JSON export | Authenticated |
| `GET` | `/api/reports/sessions/:id/exports` | List stored exports for a session | Authenticated |
| `GET` | `/api/reports/exports/:id/download` | Download a previously stored export artifact | Authenticated |
| | | | |
| `GET` | `/api/health` | Health check | Authenticated |

All list endpoints support pagination (`?page=1&per_page=25`) and return:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 25,
  "pages": 2
}
```

---

## Security

### Authentication & Authorization
- **JWT Tokens** -- Short-lived access tokens (5 min) with refresh rotation
- **HttpOnly Cookies** -- Refresh tokens stored in secure, HttpOnly, SameSite=Strict cookies
- **Authenticated Pages Only** -- Every frontend page except the login screen requires an authenticated session
- **DB-Backed Refresh Sessions** -- Active refresh-session families survive backend restarts
- **Refresh-Token Family Lifetime Cap** -- Every login starts a token family with an immutable `family_expires_at`. Rotation never extends it, so a stolen refresh token cannot be rotated indefinitely. See `FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS` (security policy, default 30 days, bounded 7–30) versus `FINDINGS_REFRESH_SESSION_RETENTION_DAYS` (DB cleanup lag for dead rows, auto-derived as 2 × the family cap) -- the two settings govern different things and should not be confused.
- **Token-Version Kill Switch** -- Logout or refresh-family revocation immediately invalidates outstanding access tokens for that user
- **bcrypt Hashing** -- Passwords hashed with bcrypt via passlib
- **RBAC** -- Three roles with server-enforced permissions
- **Client Scoping** -- `client_user` role sees only data belonging to their linked client (row-level filtering at ORM level)

### HTTP Security
- **Rate Limiting** -- 5 req/min on login, 60 req/min on API (configurable)
- **Security Headers** -- CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy, Permissions-Policy
- **CORS** -- Configurable allowed origins
- **TLS** -- Auto-provisioned via Caddy (Let's Encrypt) in production

### File Security
- **Content-Type Validation** -- Only allowed MIME types accepted (images, PDF, text, CSV, JSON, ZIP)
- **Size Limits** -- Attachment uploads are limited in both Caddy and the backend; the backend is authoritative, and the Caddy cap should be set at or slightly above it to reject oversized uploads early
- **Virus Scanning** -- ClamAV scans every upload before storage (when enabled)
- **Separated Storage Buckets** -- Evidence and generated exports are stored in different object-storage buckets
- **Proxied Downloads** -- Evidence files and stored exports are served through the backend (object storage is not exposed to the internet)

### Reporting Controls
- **Export Guardrails** -- The backend rejects oversized exports based on finding count, total input size, and generated output size
- **Stored Export Metadata** -- Each export records the export date, file name, creating user, format, size, SHA256, lock expiry, and taxonomy version used at generation time
- **Historical Taxonomy Reference** -- Stored exports are linked to the taxonomy version that was active when they were created

### Operational
- **No Cloud Dependencies** -- Fully self-hosted, EU-friendly, no US Cloud Act exposure
- **Automated Backups** -- Daily PostgreSQL dumps with configurable retention
- **Change Audit Trail** -- Per-field history on all finding modifications

---

## Backup & Recovery

### Automatic Backups

The `backup` service runs scheduled PostgreSQL dumps:

```bash
# Check backup status
docker compose logs backup

# List existing backups
docker compose exec backup ls -la /backups/

# Run a manual backup
docker compose exec backup /usr/local/bin/backup.sh
```

### Manual Backup

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

### Object Storage Backup

File attachments and generated reports are stored in SeaweedFS. Back up the `seaweedfs_data` volume separately:

```bash
# Back up the Docker volume directly
docker run --rm -v findings_seaweedfs_data:/data -v /host/backup:/backup alpine \
  tar czf /backup/seaweedfs_$(date +%Y%m%d).tar.gz /data
```

---

## Monitoring & Logging

### Structured logs

The backend emits one JSON object per log line to stdout. Level is controlled by `FINDINGS_LOG_LEVEL` (`DEBUG` | `INFO` | `WARNING` | `ERROR` | `CRITICAL`, case-insensitive; default `INFO`). Uvicorn access and error logs share the same JSON format.

Inspect live logs with:

```bash
docker compose logs -f backend | jq
```

Every service uses the `json-file` driver with rotation at 10MB × 5 files to keep disk use bounded.

### Healthchecks and startup order

`docker-compose.yml` defines healthchecks for `db` (`pg_isready`), `seaweedfs`, `clamav`, and `caddy`. The backend declares `depends_on` with `condition: service_healthy` against `db` and `seaweedfs`, so it does not attempt migrations or accept traffic until its dependencies are ready. `docker compose ps` reflects per-service health, and crashed containers restart via `restart: unless-stopped`.

### Optional health dashboard (Gatus)

An opt-in monitoring profile runs [Gatus](https://gatus.io) against every service. Configuration is fully declarative in [`monitoring/gatus.yaml`](monitoring/gatus.yaml) — no setup wizard, no admin login.

Start with monitoring enabled:

```bash
docker compose --profile monitoring up -d
```

Then open `http://127.0.0.1:${GATUS_PORT:-8080}` for the status page. Add alert channels (Slack, Discord, email, webhook) by editing `monitoring/gatus.yaml`; see the Gatus docs for syntax.

Gatus checks each service over the docker network using each image's fixed listening port, so host-side port overrides in `.env` do not need to be mirrored into the Gatus config.

---

## Project Structure

```
findings/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (auth, email, reports, storage, taxonomy, antivirus)
│   │   ├── config.py       # Settings (pydantic-settings)
│   │   ├── database.py     # Async engine & session factory
│   │   └── main.py         # FastAPI app, middleware, lifespan
│   ├── alembic/            # Database migrations
│   ├── templates/          # 25 YAML finding templates
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/        # Typed API clients
│   │   │   ├── components/ # Reusable Svelte 5 components
│   │   │   └── stores/     # Rune-based auth store
│   │   └── routes/         # SvelteKit pages
│   ├── Dockerfile
│   └── package.json
├── backup/
│   ├── backup.sh           # pg_dump + gzip + pruning
│   ├── entrypoint.sh       # Cron setup
│   └── Dockerfile
├── Caddyfile               # Reverse proxy config
├── docker-compose.yml      # All 7 services
└── README.md
```

---

## License

Self-hosted. Private use.
