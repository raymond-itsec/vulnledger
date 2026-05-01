# Architecture

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.12, FastAPI | REST API, async request handling |
| ORM | SQLAlchemy 2.0 (async) | Database models and queries |
| Database | PostgreSQL 16 | Primary data store |
| Migrations | Alembic | Database schema versioning |
| Frontend | SvelteKit 5, TypeScript | Single-page application |
| Styling | Custom CSS (CSS variables) | Theming, responsive design |
| Object Storage | SeaweedFS | S3-compatible file attachment and report export storage |
| Reverse Proxy | Caddy 2 | Auto-TLS, routing, compression |
| PDF Generation | WeasyPrint | HTML → PDF report rendering |
| Email | Mailjet (REST API) | Transactional email notifications |
| Auth | python-jose (JWT), bcrypt | Token-based auth, password hashing |
| SSO | Authlib | Optional OIDC/OpenID Connect |
| Antivirus | ClamAV + clamd | Attachment virus scanning |
| Rate Limiting | slowapi | Request throttling |
| Markdown | mistune | Server-side markdown rendering for PDF |
| Containerization | Docker, Docker Compose | Deployment and orchestration |

## High-level diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│   Browser    │─────│    Caddy     │─────│   Frontend   │
│              │     │  (reverse    │     │  (SvelteKit) │
│              │     │   proxy)     │     │  :5173       │
└──────────────┘     │  :80/:443    │     └──────────────┘
                     │              │
                     │              │     ┌──────────────┐
                     │   /api/*  ───│─────│   Backend    │
                     │              │     │  (FastAPI)   │
                     └──────────────┘     │  :8000       │
                                          │              │
                           ┌──────────────┤              ├──────────────┐
                           │              │              │              │
                           ▼              └──────┬───────┘              ▼
                     ┌──────────┐                │                ┌──────────┐
                     │ Postgres │                │                │SeaweedFS │
                     │  :5432   │                │                │  :8333   │
                     └──────────┘                │                └──────────┘
                           ▲                     │
                           │                     ▼
                     ┌──────────┐          ┌──────────┐
                     │  Backup  │          │  ClamAV  │
                     │ (cron)   │          │  :3310   │
                     └──────────┘          └──────────┘
```

## Request flow

1. All requests enter through **Caddy** (ports 80/443)
2. Requests to `/api/*` are proxied to the **FastAPI backend**
3. All other requests are proxied to the **SvelteKit frontend**
4. The backend communicates with **PostgreSQL** for data, **SeaweedFS** for files, **ClamAV** for scanning, and **Mailjet** for email
5. The **backup service** independently dumps PostgreSQL on a cron schedule

## Storage layout

- **Evidence bucket** - Uploaded finding attachments are stored in the configured object-storage evidence bucket
- **Reports bucket** - Generated PDF, CSV, and JSON exports are stored in a separate object-storage reports bucket
- **Report retention** - Newly generated reports are uploaded with one-year object-lock retention and recorded with SHA256 integrity metadata
- **Stored export downloads** - Session detail pages can list and download previously generated exports through the backend

### v0.2.0 breaking storage change

VulnLedger `v0.2.0` switched object storage to SeaweedFS. The default deployment no longer starts MinIO and does not automatically migrate old MinIO buckets or objects. Fresh deployments only need the SeaweedFS settings in `.env`. Existing deployments must either accept a fresh object store or manually copy existing MinIO objects into SeaweedFS before old attachment / report downloads work again.

## Authentication flow

1. User submits credentials → `POST /api/auth/login`
2. Backend verifies with bcrypt, returns JWT access token + sets HttpOnly refresh cookie
3. Frontend stores access token in memory (not localStorage - XSS safe)
4. On page load or after a 401, the frontend calls `POST /api/auth/refresh` using the cookie
5. Refresh rotates both tokens transparently and restores the in-memory access token from DB-backed refresh session state
6. All non-login frontend pages require authentication and redirect back to `/` when the user is signed out
7. Logout clears the refresh cookie, drops the in-memory access token, and returns the browser to the login page
8. Backend / container restarts do not invalidate active refresh-session families. Users sign in again only after logout, expiry, or detected token reuse.
9. Signed-in sessions poll the authenticated health endpoint to drive the shared availability banner. The login page performs only a one-time startup availability probe per browser tab session.

## OIDC SSO flow (optional)

1. User clicks "Sign in with SSO" → `GET /api/auth/oidc/login`
2. Redirect to Identity Provider (IdP)
3. IdP callback → `GET /api/auth/oidc/callback`
4. Backend auto-provisions user from OIDC claims if new
5. Redirect to the frontend, which restores the session from the refresh cookie

## Data model

```
Users ──────────────────────────────────────┐
  │                                         │
  │ reviewer_id                             │ linked_client_id
  ▼                                         ▼
ReviewSessions ── asset_id ── ReviewedAssets ── client_id ── Clients
  │                                                              │
  │ session_id                                                   │
  ▼                                                              │
Findings ── FindingHistory (per-field change log)                │
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

### Taxonomy model

VulnLedger uses DB-managed versioned taxonomies for:

- `risk_level`
- `remediation_status`
- `session_status`
- `asset_type`

Each taxonomy entry stores a machine value plus its label, sort order, optional color, and active state. The active taxonomy version drives live backend validation and frontend UI options. Stored exports also record the taxonomy version that was active when the artifact was generated.

### Roles

| Role | Permissions |
|---|---|
| **admin** | Full access. Manage users, edit built-in templates, all data |
| **reviewer** | Create/edit clients, assets, sessions, findings, templates. Cannot manage users |
| **client_user** | Read-only access scoped to their linked client's data only |

## Project structure

```
vulnledger/
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
│   │   ├── routes/         # SvelteKit pages
│   │   └── app.css         # Global tokens + base styles
│   ├── stylelint-plugins/  # Custom lint rules (e.g. form-control color enforcement)
│   ├── Dockerfile
│   └── package.json
├── backup/
│   ├── backup.sh           # pg_dump + gzip + encryption + pruning
│   ├── entrypoint.sh       # Cron setup + pre-flight encryption check
│   └── Dockerfile
├── docs/                   # This documentation site (mkdocs-material)
├── monitoring/             # Optional observability stack configs
├── Caddyfile               # Reverse proxy config
├── docker-compose.yml      # All services
└── README.md               # Project front door
```
