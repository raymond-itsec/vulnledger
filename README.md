# 🔒 Security Findings Manager

A self-hosted web application for managing security code review findings. Built for security consultants and teams who need to track clients, reviewed assets, code review sessions, and individual findings — with full edit history, report generation, and email notifications.

**Fully self-hostable. No US Cloud Act dependencies. Your data stays yours.**

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Data Model](#-data-model)
- [Local Development Setup](#-local-development-setup)
- [Production / Distributed Deployment](#-production--distributed-deployment)
- [Configuration Reference](#-configuration-reference)
- [Finding Templates](#-finding-templates)
- [API Overview](#-api-overview)
- [Security](#-security)
- [Backup & Recovery](#-backup--recovery)

---

## ✨ Features

### Core
- 👥 **Client Management** — Track clients with contact details and linked assets
- 🖥️ **Asset Tracking** — Catalog reviewed assets (web apps, APIs, mobile apps, infrastructure, etc.)
- 📝 **Review Sessions** — Organize findings per engagement with reviewer assignment and status tracking
- 🔍 **Finding Management** — Full CRUD with risk levels (critical → informational), remediation statuses, markdown-rich descriptions, and file attachments
- 📜 **Change History** — Per-field audit trail on every finding edit (who changed what, when)
- 📎 **File Attachments** — Upload screenshots, evidence, and documents (stored in MinIO)

### Templates
- 📋 **25 Built-in Finding Templates** — Covering OWASP Top 10 categories: injection, authentication, access control, cryptography, misconfiguration, and more
- ✏️ **Custom Templates** — Create, edit, and delete your own finding templates
- 🔄 **YAML-based Sync** — Built-in templates managed via YAML files, idempotent sync on startup

### Reporting & Notifications
- 📄 **PDF Reports** — Professional, styled security review reports with executive summary, risk breakdown, and detailed findings (WeasyPrint)
- 📊 **CSV Export** — Spreadsheet-friendly export of all findings per session
- 📦 **JSON Export** — Structured data export for integration with other tools
- 📧 **Email Notifications** — Via Mailjet: new finding alerts, status change notifications, report-ready notifications

### Dashboard
- 📈 **Risk Level Breakdown** — Visual bar charts of findings by severity
- 📊 **Status Breakdown** — At-a-glance remediation progress
- 🔗 **Quick Actions** — One-click access to create clients, findings
- 🕐 **Recent Activity** — Latest sessions and findings

### Security & Operations
- 🔐 **JWT Authentication** — Access tokens (15 min) + HttpOnly refresh token cookies (7 days)
- 👤 **Role-Based Access Control** — Admin, Reviewer, Client User roles with data isolation
- 🚦 **Rate Limiting** — Brute-force protection on login, configurable API limits
- 🛡️ **Security Headers** — CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- 🔑 **Optional OIDC SSO** — Integrate with any OpenID Connect provider (Keycloak, Azure AD, Okta, etc.)
- 🦠 **Virus Scanning** — ClamAV integration scans every file upload before storage and blocks uploads if the scanner is configured but unavailable
- 💾 **Automated Backups** — Scheduled PostgreSQL dumps with configurable retention

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12, FastAPI | REST API, async request handling |
| **ORM** | SQLAlchemy 2.0 (async) | Database models and queries |
| **Database** | PostgreSQL 16 | Primary data store |
| **Migrations** | Alembic | Database schema versioning |
| **Frontend** | SvelteKit 5, TypeScript | Single-page application |
| **Styling** | Custom CSS (CSS variables) | Theming, responsive design |
| **Object Storage** | MinIO | S3-compatible file attachment storage |
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

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│   Browser    │────▶│    Caddy     │────▶│   Frontend   │
│              │     │  (reverse    │     │  (SvelteKit) │
│              │     │   proxy)     │     │  :5173       │
└──────────────┘     │  :80/:443   │     └──────────────┘
                     │              │
                     │              │     ┌──────────────┐
                     │   /api/*  ───│────▶│   Backend    │
                     │              │     │  (FastAPI)   │
                     └──────────────┘     │  :8000       │
                                          │              │
                           ┌──────────────┤              ├──────────────┐
                           │              │              │              │
                           ▼              └──────┬───────┘              ▼
                     ┌──────────┐                │                ┌──────────┐
                     │ PostgreSQL│                │                │  MinIO   │
                     │  :5432   │                │                │  :9000   │
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
4. The backend communicates with **PostgreSQL** for data, **MinIO** for files, **ClamAV** for scanning, and **Mailjet** for email
5. The **backup service** independently dumps PostgreSQL on a cron schedule

### Authentication Flow
1. User submits credentials → `POST /api/auth/login`
2. Backend verifies with bcrypt, returns JWT access token + sets HttpOnly refresh cookie
3. Frontend stores access token in memory (not localStorage — XSS safe)
4. On page load or after a 401, the frontend calls `POST /api/auth/refresh` using the cookie
5. Refresh rotates both tokens transparently and restores the in-memory access token

### OIDC SSO Flow (Optional)
1. User clicks "Sign in with SSO" → `GET /api/auth/oidc/login`
2. Redirect to Identity Provider (IdP)
3. IdP callback → `GET /api/auth/oidc/callback`
4. Backend auto-provisions user from OIDC claims if new
5. Redirect to the frontend, which restores the session from the refresh cookie

---

## 💾 Data Model

```
Users ──────────────────────────────────────┐
  │                                         │
  │ reviewer_id                             │ linked_client_id
  ▼                                         ▼
ReviewSessions ◀── asset_id ── ReviewedAssets ◀── client_id ── Clients
  │                                                              │
  │ session_id                                                   │
  ▼                                                              │
Findings ──▶ FindingHistory (per-field change log)               │
  │                                                              │
  │ finding_id                                      Users.linked_client_id
  ▼                                    (client_user sees only their client's data)
FindingAttachments (MinIO)

FindingTemplates (25 built-in + custom)
```

### Roles
| Role | Permissions |
|------|------------|
| **admin** | Full access. Manage users, edit built-in templates, all data |
| **reviewer** | Create/edit clients, assets, sessions, findings, templates. Cannot manage users |
| **client_user** | Read-only access scoped to their linked client's data only |

---

## 🖥️ Local Development Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) v2+
- [Node.js](https://nodejs.org/) 22+ (for frontend development)
- [Python](https://www.python.org/) 3.12+ (for backend development)

### Quick Start (Docker — recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url> findings
cd findings

# 2. Create your local environment file
cp .env.example .env

# 3. Review the secrets and initial admin values in .env

# 4. Start all services
docker compose up -d

# 5. Open in browser
open http://localhost
```

That's it. The app will be available at `http://localhost` with:
- 📌 Your configured initial admin account from `.env`
- 📌 25 finding templates auto-synced on startup
- 📌 PostgreSQL, MinIO, and all services running

### Development Mode (hot reload)

If you want to develop with live reloading on both frontend and backend:

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies (WeasyPrint needs system libs — see below)
pip install -r requirements.txt

# Start PostgreSQL (if not using Docker)
# Ensure FINDINGS_DATABASE_URL points to your local PostgreSQL

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

> ⚠️ **WeasyPrint system dependencies** (required for PDF generation):
> - **macOS:** `brew install pango libffi cairo glib`
> - **Ubuntu/Debian:** `apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2`
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
# Start only PostgreSQL and MinIO
docker compose up -d db minio

# Optional: Start ClamAV for virus scanning
docker compose up -d clamav
```

### Environment Variables

Create a `.env` file in the project root (or set environment variables):

```env
# Required
FINDINGS_DATABASE_URL=postgresql+asyncpg://findings:findings@localhost:5432/findings
FINDINGS_SECRET_KEY=change-this-jwt-signing-key
FINDINGS_INITIAL_ADMIN_USERNAME=admin
FINDINGS_INITIAL_ADMIN_PASSWORD=change-this-admin-password
FINDINGS_INITIAL_ADMIN_EMAIL=admin@example.com

# MinIO (file attachments)
FINDINGS_MINIO_ENDPOINT=localhost:9000
FINDINGS_MINIO_ACCESS_KEY=findings-storage
FINDINGS_MINIO_SECRET_KEY=change-this-minio-secret

# Optional: Email notifications
FINDINGS_MAILJET_API_KEY=your-mailjet-key
FINDINGS_MAILJET_API_SECRET=your-mailjet-secret
FINDINGS_MAILJET_FROM_EMAIL=security@yourcompany.com
FINDINGS_APP_BASE_URL=http://localhost

# Optional: OIDC SSO
FINDINGS_OIDC_ENABLED=false
FINDINGS_OIDC_CLIENT_ID=
FINDINGS_OIDC_CLIENT_SECRET=
FINDINGS_OIDC_DISCOVERY_URL=
FINDINGS_OIDC_REDIRECT_URI=

# Optional: ClamAV
FINDINGS_CLAMAV_HOST=localhost
FINDINGS_CLAMAV_PORT=3310
```

---

## 🚀 Production / Distributed Deployment

### Single-Server Deployment (Docker Compose)

This is the recommended approach for most teams.

```bash
# 1. Clone to your server
git clone <your-repo-url> /opt/findings
cd /opt/findings

# 2. Configure environment
cp .env.example .env
nano .env  # Set production values (see below)

# 3. Set your public host in .env
# CADDY_HOST=yourdomain.com
```

> 💡 Caddy automatically provisions and renews Let's Encrypt TLS certificates when `CADDY_HOST` is set to a public domain. The default `http://localhost` value keeps local development simple.

```bash
# 4. Start all services
docker compose up -d

# 5. Verify everything is running
docker compose ps
docker compose logs -f backend  # Watch for startup messages
```

### Production Environment Variables

These **must** be changed from defaults:

```env
# ⚠️ CRITICAL — change these!
FINDINGS_SECRET_KEY=<random-64-char-string>
MINIO_ROOT_USER=<strong-access-key>
MINIO_ROOT_PASSWORD=<strong-secret-key>
FINDINGS_INITIAL_ADMIN_USERNAME=<admin-username>
FINDINGS_INITIAL_ADMIN_PASSWORD=<strong-admin-password>
FINDINGS_INITIAL_ADMIN_EMAIL=<admin-email>

# Database (use strong password)
POSTGRES_PASSWORD=<strong-db-password>
FINDINGS_DATABASE_URL=postgresql+asyncpg://findings:<strong-db-password>@db:5432/findings

# Your public URL (used in emails and OIDC redirects)
FINDINGS_APP_BASE_URL=https://yourdomain.com

# Email (Mailjet — sign up at mailjet.com)
FINDINGS_MAILJET_API_KEY=<your-key>
FINDINGS_MAILJET_API_SECRET=<your-secret>
FINDINGS_MAILJET_FROM_EMAIL=security@yourdomain.com
```

### Multi-Server / Distributed Deployment

For larger teams or high-availability requirements, you can split services across multiple machines.

#### Database Server
```bash
# Run PostgreSQL separately with proper tuning
docker run -d \
  --name findings-db \
  --restart unless-stopped \
  -e POSTGRES_USER=findings \
  -e POSTGRES_PASSWORD=<strong-password> \
  -e POSTGRES_DB=findings \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine \
  -c shared_buffers=256MB \
  -c work_mem=16MB \
  -c max_connections=100
```

#### Storage Server (MinIO)
```bash
# Run MinIO with encryption at rest
docker run -d \
  --name findings-minio \
  --restart unless-stopped \
  -e MINIO_ROOT_USER=<access-key> \
  -e MINIO_ROOT_PASSWORD=<secret-key> \
  -v minio_data:/data \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio server /data --console-address ":9001"
```

#### Application Server
```bash
# Backend
docker run -d \
  --name findings-backend \
  --restart unless-stopped \
  -e FINDINGS_DATABASE_URL=postgresql+asyncpg://findings:<pw>@<db-host>:5432/findings \
  -e FINDINGS_SECRET_KEY=<secret> \
  -e FINDINGS_MINIO_ENDPOINT=<minio-host>:9000 \
  -e FINDINGS_MINIO_ACCESS_KEY=<key> \
  -e FINDINGS_MINIO_SECRET_KEY=<secret> \
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
  -e POSTGRES_USER=findings \
  -e POSTGRES_PASSWORD=<pw> \
  -e POSTGRES_DB=findings \
  -e BACKUP_RETENTION_DAYS=90 \
  -e BACKUP_CRON="0 2 * * *" \
  -v /mnt/backup-storage:/backups \
  findings-backup
```

### Docker Compose (Production) — All Services

The default `docker-compose.yml` runs all 7 services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `db` | postgres:16-alpine | `127.0.0.1:5432` | Primary database |
| `minio` | minio/minio | `127.0.0.1:9000`, `127.0.0.1:9001` | Object storage for attachments |
| `backend` | Custom (Python 3.12) | `127.0.0.1:8000` | FastAPI REST API |
| `frontend` | Custom (Node 22) | `127.0.0.1:5173` | SvelteKit SPA |
| `caddy` | caddy:2.11.2-alpine | `80`, `443`, `443/udp` | Reverse proxy with optional auto-TLS |
| `backup` | Custom (postgres + cron) | — | Scheduled database backups |
| `clamav` | clamav/clamav:stable | `127.0.0.1:3310` | Antivirus scanning |

### Volumes

| Volume | Data | Backup? |
|--------|------|---------|
| `pgdata` | PostgreSQL data | ✅ Auto-backed up by backup service |
| `minio_data` | File attachments | ⚠️ Back up separately or use MinIO replication |
| `backups` | SQL dump files | 📁 Mount to host or NFS for off-server storage |
| `caddy_data` | TLS certificates | 🔄 Auto-managed by Caddy |
| `clamav_data` | Virus definitions | 🔄 Auto-updated by ClamAV |

---

## ⚙️ Configuration Reference

All settings use the `FINDINGS_` prefix and can be set via environment variables or `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `FINDINGS_DATABASE_URL` | `postgresql+asyncpg://findings:findings@db:5432/findings` | PostgreSQL connection string |
| `FINDINGS_SECRET_KEY` | _(empty)_ | JWT signing key (required) |
| `FINDINGS_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `FINDINGS_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `FINDINGS_ALLOWED_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | CORS allowed origins |
| `FINDINGS_MINIO_ENDPOINT` | `minio:9000` | MinIO server address |
| `FINDINGS_MINIO_ACCESS_KEY` | _(empty)_ | MinIO access key |
| `FINDINGS_MINIO_SECRET_KEY` | _(empty)_ | MinIO secret key |
| `FINDINGS_MINIO_SECURE` | `false` | Use HTTPS for MinIO |
| `FINDINGS_MAILJET_API_KEY` | _(empty)_ | Mailjet API key (empty = emails disabled) |
| `FINDINGS_MAILJET_API_SECRET` | _(empty)_ | Mailjet API secret |
| `FINDINGS_MAILJET_FROM_EMAIL` | `noreply@findings.local` | Sender email address |
| `FINDINGS_MAILJET_FROM_NAME` | `Security Findings Manager` | Sender display name |
| `FINDINGS_APP_BASE_URL` | `http://localhost` | Public URL (used in emails and redirects) |
| `FINDINGS_RATE_LIMIT_LOGIN` | `5/minute` | Login endpoint rate limit |
| `FINDINGS_RATE_LIMIT_API` | `60/minute` | Default API rate limit |
| `FINDINGS_OIDC_ENABLED` | `false` | Enable OIDC SSO |
| `FINDINGS_OIDC_CLIENT_ID` | _(empty)_ | OIDC client ID |
| `FINDINGS_OIDC_CLIENT_SECRET` | _(empty)_ | OIDC client secret |
| `FINDINGS_OIDC_DISCOVERY_URL` | _(empty)_ | OIDC discovery URL (`.well-known/openid-configuration`) |
| `FINDINGS_OIDC_REDIRECT_URI` | _(empty)_ | OIDC callback URL |
| `FINDINGS_OIDC_DEFAULT_ROLE` | `reviewer` | Default role for auto-provisioned SSO users |
| `FINDINGS_INITIAL_ADMIN_USERNAME` | _(empty)_ | Username for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_PASSWORD` | _(empty)_ | Password for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_EMAIL` | _(empty)_ | Email for the one-time seeded admin account |
| `FINDINGS_INITIAL_ADMIN_FULL_NAME` | `Administrator` | Display name for the one-time seeded admin account |
| `FINDINGS_CLAMAV_HOST` | _(empty)_ | ClamAV host (empty = scanning disabled) |
| `FINDINGS_CLAMAV_PORT` | `3310` | ClamAV TCP port |

### Backup Configuration

Set on the `backup` service (not `FINDINGS_` prefix):

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_CRON` | `0 2 * * *` | Cron schedule (default: daily 2 AM) |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep old backups |

---

## 📋 Finding Templates

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

## 🌐 API Overview

All endpoints are prefixed with `/api`. Authentication is via Bearer token in the `Authorization` header.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/login` | Login, get access token | Public |
| `POST` | `/api/auth/refresh` | Refresh access token | Cookie |
| `POST` | `/api/auth/logout` | Clear refresh cookie | Public |
| `GET` | `/api/auth/oidc/login` | Start OIDC flow | Public |
| `GET` | `/api/auth/oidc/callback` | OIDC callback | Public |
| | | | |
| `GET` | `/api/users` | List users | Admin |
| `GET` | `/api/users/me` | Current user profile | Any |
| `POST` | `/api/users` | Create user | Admin |
| | | | |
| `GET` | `/api/clients` | List clients | Any |
| `POST` | `/api/clients` | Create client | Admin/Reviewer |
| `GET` | `/api/clients/:id` | Get client | Any |
| `PATCH` | `/api/clients/:id` | Update client | Admin/Reviewer |
| | | | |
| `GET` | `/api/assets` | List assets | Any |
| `POST` | `/api/assets` | Create asset | Admin/Reviewer |
| `GET` | `/api/assets/:id` | Get asset | Any |
| `PATCH` | `/api/assets/:id` | Update asset | Admin/Reviewer |
| | | | |
| `GET` | `/api/sessions` | List sessions | Any |
| `POST` | `/api/sessions` | Create session | Admin/Reviewer |
| `GET` | `/api/sessions/:id` | Get session | Any |
| `PATCH` | `/api/sessions/:id` | Update session | Admin/Reviewer |
| | | | |
| `GET` | `/api/findings` | List findings (filterable) | Any |
| `POST` | `/api/findings` | Create finding | Admin/Reviewer |
| `GET` | `/api/findings/:id` | Get finding | Any |
| `PATCH` | `/api/findings/:id` | Update finding | Admin/Reviewer |
| `GET` | `/api/findings/:id/history` | Get change history | Any |
| | | | |
| `GET` | `/api/findings/:id/attachments` | List attachments | Any |
| `POST` | `/api/findings/:id/attachments` | Upload file | Admin/Reviewer |
| `GET` | `/api/attachments/:id/download` | Download file | Any |
| `DELETE` | `/api/attachments/:id` | Delete file | Admin/Reviewer |
| | | | |
| `GET` | `/api/templates` | List templates | Any |
| `POST` | `/api/templates` | Create template | Admin/Reviewer |
| `GET` | `/api/templates/:id` | Get template | Any |
| `PATCH` | `/api/templates/:id` | Update template | Admin/Reviewer |
| `DELETE` | `/api/templates/:id` | Delete template | Admin/Reviewer |
| | | | |
| `GET` | `/api/reports/sessions/:id/pdf` | Download PDF report | Any |
| `GET` | `/api/reports/sessions/:id/csv` | Download CSV export | Any |
| `GET` | `/api/reports/sessions/:id/json` | Download JSON export | Any |
| | | | |
| `GET` | `/api/health` | Health check | Public |

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

## 🔐 Security

### Authentication & Authorization
- **JWT Tokens** — Short-lived access tokens (15 min) with refresh rotation
- **HttpOnly Cookies** — Refresh tokens stored in secure, HttpOnly, SameSite=Strict cookies
- **bcrypt Hashing** — Passwords hashed with bcrypt via passlib
- **RBAC** — Three roles with server-enforced permissions
- **Client Scoping** — `client_user` role sees only data belonging to their linked client (row-level filtering at ORM level)

### HTTP Security
- **Rate Limiting** — 5 req/min on login, 60 req/min on API (configurable)
- **Security Headers** — CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy, Permissions-Policy
- **CORS** — Configurable allowed origins
- **TLS** — Auto-provisioned via Caddy (Let's Encrypt) in production

### File Security
- **Content-Type Validation** — Only allowed MIME types accepted (images, PDF, text, CSV, JSON, ZIP)
- **Size Limits** — 25 MB max per file
- **Virus Scanning** — ClamAV scans every upload before storage (when enabled)
- **Proxied Downloads** — Files served through the backend (MinIO not exposed to internet)

### Operational
- **No Cloud Dependencies** — Fully self-hosted, EU-friendly, no US Cloud Act exposure
- **Automated Backups** — Daily PostgreSQL dumps with configurable retention
- **Change Audit Trail** — Per-field history on all finding modifications

---

## 💾 Backup & Recovery

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

### MinIO Backup

File attachments are stored in MinIO. Back up the `minio_data` volume separately:

```bash
# Copy MinIO data
docker compose exec minio mc mirror /data /backup-destination

# Or back up the Docker volume directly
docker run --rm -v findings_minio_data:/data -v /host/backup:/backup alpine \
  tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

---

## 📁 Project Structure

```
findings/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── models/         # SQLAlchemy models (9 models)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (auth, email, reports, storage, antivirus)
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

## 📄 License

Self-hosted. Private use.
