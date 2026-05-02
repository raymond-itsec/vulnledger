# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Active work tracks under v0.3.0 below. Open issues for the next release line live on GitHub with the [`v0.3.x` label](https://github.com/raymond-itsec/vulnledger/labels/v0.3.x).

## [v0.3.0] - Planned (breaking)

This is the planned next-major shape of the project. **No upgrade scripts will be provided** for the changes below; deployments running v0.2.x must redeploy from scratch on the new layout.

It's only "breaking" in the deployment sense, not the data sense. The migration path is: take a fresh backup on v0.2.x, deploy v0.3.0 from scratch, restore.

**What survives a fresh v0.3.0 deploy + restore**:

- Application **database** (clients, assets, sessions, findings, finding history, taxonomy, users, invites, report-export metadata) — recoverable from any encrypted `findings_*.sql.gz.enc` produced by the `backup` container.

**What does NOT survive automatically**:

- **Object storage** (`seaweedfs_data` volume): finding attachments and the actual stored PDF/CSV/JSON report-export bytes. v0.2.x's `backup` container only handles PostgreSQL. The SeaweedFS volume must be snapshotted manually before the v0.3.0 fresh deploy if attachments and stored exports need to survive. See [Operations → Object storage backup](https://raymond-itsec.github.io/vulnledger/operations/#object-storage-backup) for the manual `tar` procedure.

Long-term, multi-node SeaweedFS replication will replace the manual snapshot path.

### Planned breaking changes
- Per-tier docker compose layout (`compose/edge.yml`, `compose/app.yml`, `compose/data.yml`, `compose/monitoring.yml`) replacing the single `docker-compose.yml`. Existing `docker-compose.yml` retired in favor of a Makefile-driven `make allinone-up` / `make multihost-up`.
- Multi-host topology with WireGuard mesh between four hosts (edge, app, data, monitoring). Single-host `allinone` mode preserved as a profile.
- VictoriaMetrics + vmagent + vmalert + Alertmanager + Grafana + Loki replace Gatus for observability. Internal Grafana dashboards via SSO; public anonymous dashboard for the customer-facing status page.
- Tier-isolated docker networks (`edge_net`, `app_net`, `data_net`, `monitoring_net`) replacing the single shared bridge.
- Service discovery via env-driven hostnames (`data.vl.local`, `app.vl.local`, etc.) instead of bare docker service names.
- DB schema rename per the Q1(b) redesign decision: `Clients` table → `Customers`, `ReviewSessions` table → `Projects`. API routes follow: `/api/clients` → `/api/customers`, `/api/sessions` → `/api/projects`. Touches backend models, alembic migration, API routes, frontend routes, and the API client. Migration runs automatically during the v0.3.0 fresh-deploy + restore flow.

### Changed
- **Breaking (API):** standardized pagination shape across all list endpoints. Five list endpoints that previously returned bare arrays or bespoke envelopes now return the standard `{items, total, page, per_page, pages}` shape used by every other list endpoint. Frontend updated in lockstep:
  - `GET /api/findings/{id}/attachments` — was bare array, now paginated (`page`, `per_page` query params, default 25, max 100).
  - `GET /api/taxonomy/versions` — was bare array, now paginated (default 50, max 200).
  - `GET /api/users/reviewers` — was bare array, now paginated (default 100, max 200).
  - `GET /api/auth/sessions` — was `{items}` only, now full envelope (default 50, max 200).
  - `GET /api/auth/security-events` — was `{items, limit}`, now full envelope. The `limit` query param is renamed to `per_page` (same semantics, ge=1, le=200).
  - Removed obsolete `SessionListResponse` and `SecurityEventListResponse` Pydantic schemas; both endpoints now declare `PaginatedResponse[SessionInfo]` / `PaginatedResponse[SecurityEventInfo]` directly.

### Fixed
- Replaced two `datetime.utcnow()` calls in `backend/app/services/reports.py` with `datetime.now(timezone.utc)`. The deprecated `utcnow()` returned a naive datetime that lost the UTC marker on JSON serialization (consumers parsing `report_generated_at` would have seen no `+00:00` suffix and could mis-interpret the timestamp as local time). All 21 Postgres datetime columns already use `TIMESTAMP WITH TIME ZONE`.
- SeaweedFS volume cap bumped from the default 8 to 100 in `docker-compose.yml`. The default was hit by the existing default-collection volumes (1-7, holding filer metadata + S3 bucket configs) plus the `generated-reports` collection volume (volume 8), leaving no headroom for the master to allocate a volume for the `finding-attachments` collection. Every attachment upload since the storage migration was failing silently with `No writable volumes and no free volumes left for collection:finding-attachments` in the SeaweedFS logs. SeaweedFS hardcodes growth = 7 volumes per event for replication "000" (`Copy1Count` in `weed/topology/volume_growth.go`); not configurable in 4.20. So 3 active collections × 7 = 21 at boot, +7 per regrowth. Cap of 100 gives ~11 growth events of headroom. Each volume is up to ~30GB, allocated lazily, so the higher cap costs nothing if unused.

### Audited (no code change required)
- httpx connection-reuse audit: zero direct uses of `httpx` in application code (`backend/app/`, `backend/tests/`, `backend/scripts/`). `httpx==0.28.1` is a transitive dependency pinned for Authlib's OIDC discovery + token exchange; Authlib manages its own client lifecycle. No connection-pool leak risk to refactor. Added an explanatory comment in `backend/requirements.txt` so the pin isn't accidentally removed by a future cleanup.

## [v0.2.2] - 2026-05-01

### Security
- Fixed VL-2026-012 ([#23](https://github.com/raymond-itsec/vulnledger/issues/23)): login rate-limit bypass via path normalization. Added `@malformed_path` matcher in Caddy using `vars_regexp` against `{http.request.orig_uri.path}` to reject paths containing `//`, `/./`, `/../`, `%2F`, `%5C`, or NUL bytes (encoded or literal) with 400 before any handler runs. Tightened `@login_brute` to anchored regexp `(?i)^/api/auth/login/?$` as belt-and-braces.
- Fixed VL-2026-014 ([#31](https://github.com/raymond-itsec/vulnledger/issues/31)): hardcoded the session-hint cookie name (`vl_session`) in the backend instead of leaving it env-configurable. Eliminates the drift between backend (env-driven) and Caddy (hardcoded) that could break the auth gate when the env was changed. Removed `FINDINGS_SESSION_HINT_COOKIE_NAME` from `config.py`, `docker-compose.yml`, `.env.example`, README, and the `security-audit` CI workflow.
- Fixed VL-2026-015 ([#32](https://github.com/raymond-itsec/vulnledger/issues/32)): admin user create/update payload validation. Three sub-issues:
  - Added `zxcvbn` strength estimation on every password entry point (onboarding, admin user create) via new shared validator at `backend/app/services/password_policy.py`. Catches long-but-weak passwords (`aaaaaaaaaaaaaaaa`, `passwordpassword`).
  - Constrained `role` on `UserCreate` and `UserUpdate` to `Literal['admin', 'reviewer', 'client_user']`. Garbage role strings now return 422 instead of soft-locking the account.
  - Wrapped commits in `create_user` and `update_user` with `try/except IntegrityError -> 409`. Duplicate username/email no longer returns 500.
- Added password policy settings: `FINDINGS_PASSWORD_MIN_LENGTH` (default 16, hard floor enforced via `Field(ge=16)`), `FINDINGS_PASSWORD_MAX_LENGTH` (default 128), `FINDINGS_PASSWORD_MIN_ZXCVBN_SCORE` (default 3). Cross-field model validator on `Settings` rejects misconfigs (e.g., max < min) at startup with a clear message.
- Hardened the backup container: pre-flight encryption check in `entrypoint.sh` runs before the scheduler. Missing passphrase in production mode prints a loud actionable banner and exits 78 (SYSEXITS configuration error). Restart policy changed from `unless-stopped` to `"no"` so config errors surface in `docker compose ps` instead of looping silently. Closes [#26](https://github.com/raymond-itsec/vulnledger/issues/26).
- Disabled SeaweedFS filer directory listing (`-filer.disableDirListing`) and removed the LAN port binding for the filer UI. Backend still talks to seaweedfs over the docker network; nothing else needs port 8888 reachable.
- Added `clipboard-write=(self)` to the Caddy `Permissions-Policy` header so the new SHA256 copy-to-clipboard button can use the modern API.

### Added
- New `mkdocs-material` documentation site auto-published to GitHub Pages via `.github/workflows/docs.yml`. Eight pages: Home, Quickstart, Architecture, Deployment, Operations, Configuration, Security (with the findings register), API Reference.
- New `.github/FUNDING.yml` adds a Sponsor button at the top of the repository (GitHub Sponsors).
- New custom stylelint rule `vl/no-form-bg-without-color` flags any selector targeting `input/textarea/select` that sets `background` without an explicit `color`. Mechanically prevents the recurring white-on-white form input regression class. Wired into `.github/workflows/frontend-lint.yml` to run on push and pull request. Closes [#29](https://github.com/raymond-itsec/vulnledger/issues/29).
- Added SHA256 copy-to-clipboard button on the Stored Exports table. New `frontend/src/lib/util/clipboard.ts` helper tries `navigator.clipboard.writeText` first and falls back to `document.execCommand('copy')` for plain-HTTP origins.
- Added the `internal-audit` GitHub label to mark every self-reported finding from internal audit sweeps.

### Changed
- Replaced the dated `audit-YYYY-MM-DD` GitHub label scheme with the single `internal-audit` label. Migrated 15 existing issues. Date stays in the issue body / register row.
- Slimmed `README.md` from 972 lines to 22 (tagline + docs link + sponsor link + license). All long-form content lives at the docs site now.
- Replaced the global `code, .code` styling with a pastel-friendly tint (`rgba(120, 100, 160, 0.10)` background, `var(--text-primary)` text). Was dark-on-dark and unreadable in every place inline code was used (SHA columns, invite codes).
- Restyled the modal component to match the pastel-glass aesthetic: glass-card surface, sticky frosted header, softer overlay with backdrop blur, hover state on close button.
- Added thin lavender semi-transparent scrollbars globally (`::-webkit-scrollbar` + Firefox `scrollbar-color`) to replace the OS-default black scrollbars that broke the visual language inside modals and textareas.
- AppTopbar `.search input` color literal swapped to `var(--text-primary)`. WaitlistLandingPage `--ink` local token removed; references updated to `--text-primary`. Token consistency.
- AppSidebar `isActive()` and the layout breadcrumb match now use longest-prefix logic instead of greedy `find()`. Dashboard no longer falsely highlights as active on every `/app/<sub>` page. Fixes VL-2026-011 broader than the original error-page-only scope.

### Fixed
- Fixed VL-2026-010 ([#20](https://github.com/raymond-itsec/vulnledger/issues/20)): `POST /api/findings` 500 caused by nested transaction begin. Replaced `async with db.begin():` blocks in `create_finding` and `update_finding` with the codebase convention (`db.add(...)` -> `await db.commit()`).
- Fixed VL-2026-013 ([#24](https://github.com/raymond-itsec/vulnledger/issues/24)): Caddy attachment body-cap matcher. The previous `request_body /api/findings/*/attachments` glob did not match the canonical upload path; real uploads >1MB silently 413'd at the edge. Now uses two `request_body` directives with mutually exclusive `path_regexp` matchers (`@attachments` and `@not_attachments`) so exactly one fires per request.
- Fixed VL-2026-011 ([#21](https://github.com/raymond-itsec/vulnledger/issues/21), broader than the original report): sidebar active state and breadcrumb both mis-derived on every `/app/<sub>` page (Dashboard always highlighted, breadcrumb showed `Dashboard / Detail`). Greedy prefix matching replaced with longest-prefix matching in both places.
- Fixed [#28](https://github.com/raymond-itsec/vulnledger/issues/28): white-on-white input text recurring regression. Added `color: var(--text-primary)` and `background: #ffffff` to the bare `input, select, textarea` rule in `app.css`. Added `:-webkit-autofill` rules pinning text and background to our tokens. Added explicit `color` on the scoped `.md-editor textarea` rule. Future-proofed by the new stylelint rule ([#29](https://github.com/raymond-itsec/vulnledger/issues/29)).

### Removed
- Removed Gatus from the stack. The `gatus` service definition is gone from `docker-compose.yml`, the `monitoring/gatus.yaml` and `monitoring/` directory are deleted, `GATUS_PORT` and `GATUS_BIND_IP` are removed from `.env.example`, and the "Optional health dashboard" section is removed from `docs/operations.md`. Gatus will be replaced by the VictoriaMetrics + Grafana + Loki + Alertmanager stack landing as part of v0.3.0. Past releases keep their Gatus mentions in the historical CHANGELOG entries.
- Removed the `FINDINGS_SESSION_HINT_COOKIE_NAME` configuration setting (see VL-2026-014 / [#31](https://github.com/raymond-itsec/vulnledger/issues/31) above).

### Operations
- Created `docs/SECURITY-FINDINGS.md` register with `VL-YYYY-NNN` IDs. Convention codified: behavior-affecting findings get VL-IDs and a register row; pure code-hygiene work stays as plain enhancement issues.
- Added new GitHub issues for follow-up enhancement work tracked separately: [#22](https://github.com/raymond-itsec/vulnledger/issues/22) (centralize `COOKIE_SECURE` derivation), [#25](https://github.com/raymond-itsec/vulnledger/issues/25) (swap healthcheck to `/api/health/live`), [#27](https://github.com/raymond-itsec/vulnledger/issues/27) (expand observability stack), [#30](https://github.com/raymond-itsec/vulnledger/issues/30) (implement workspace search), [#33](https://github.com/raymond-itsec/vulnledger/issues/33) (per-role password length tiers).

## [v0.2.1] - 2026-04-30

### Breaking
- Moved the authenticated app entry from `/` to `/app`. The public root now serves the waitlist page, and the dedicated sign-in page now lives at `/login`.

### Added
- Added invite-gated onboarding with new backend endpoints for invite verification, onboarding state, and account completion.
- Added invite persistence with an `invites` table and onboarding cookie validation that binds account creation to the invited email address.
- Added admin invite creation, listing, and revocation so clean installs can issue one-email invite codes without manual database edits.
- Added public frontend routes for `/invite`, `/onboarding`, `/login`, and `/app`.
- Added `PublicHeader`, `PublicFooter`, and `PublicShell` shared Svelte components for all public-facing pages.
- Added footer navigation row with eight short-URL links: `/about`, `/help`, `/trust`, `/privacy`, `/terms`, `/guidelines`, `/contact`, `/support`.
- Added stub pages for all eight footer links with placeholder content and consistent branding.

### Changed
- Ported the Worker waitlist experience into the real frontend app for `/`, including waitlist signup and an invite-code CTA.
- Split the old root login/dashboard page into dedicated login and dashboard pages.
- Centralized the frontend app base path behind a shared route helper so `/app` links and redirects are easier to maintain.
- Updated auth redirects and layout guards so public pages stay public, onboarding requires a verified invite, and authenticated users land in `/app`.
- Changed the invite flow handoff to `/invite` -> `/onboarding` -> `/login` -> `/app`, with onboarding now creating the account and then returning the user to the standard sign-in flow.
- Added `/app/...` route wrappers for the existing application pages while keeping the old top-level URLs working as compatibility routes during the transition.
- Unified admin-issued invites and waitlist-approved invites on the same backend invite system so both flows can mint codes for onboarding.
- Replaced inline nav and footer in `WaitlistLandingPage` with shared `PublicHeader` and `PublicFooter` components.
- Refactored login, invite, and onboarding pages to use `PublicShell` instead of per-page background and centering styles.
- Registered all new public routes in the layout auth guard so they bypass the authentication redirect.
- Removed hardcoded version fallbacks from `frontend/Dockerfile` (stale `0.1.16`), `docker-compose.yml` (`:-0.2.0` defaults), and `backend/app/config.py` (`"0.2.0"` default); `package.json` is now the sole frontend version source of truth.

## [v0.2.0] - 2026-04-28

### Breaking
- Replaced MinIO with a fresh SeaweedFS S3-compatible object-storage deployment. Existing MinIO object data is not migrated automatically; upgrades must start with SeaweedFS storage or migrate objects manually before old attachment/report downloads will work.
- Removed app-facing MinIO configuration from the default deployment path. Use `FINDINGS_OBJECT_STORAGE_*`, `SEAWEEDFS_S3_ACCESS_KEY`, and `SEAWEEDFS_S3_SECRET_KEY`; old `FINDINGS_MINIO_*` / `MINIO_*` values are no longer wired into Compose.
- Removed `FINDINGS_DATABASE_URL` from the default deployment path. The backend now builds the connection string from `POSTGRES_HOST`, `POSTGRES_SERVICE_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.
- Made initial admin credentials and object-storage credentials mandatory in the default deployment path. Missing values now fail fast at startup.
- Removed HS256 JWT support from the runtime path. RS256 key configuration is now required, and `FINDINGS_SECRET_KEY`, `FINDINGS_JWT_PRIMARY_ALGORITHM`, and `FINDINGS_JWT_ALLOW_LEGACY_HS256` are no longer used.
- Removed legacy password-hash verification for plain bcrypt and `bcrypt-sha256 v1`. Only the current `bcrypt-sha256 v2` path is accepted.

### Changed
- Updated stack version defaults to `0.2.0`.
- Refactored repeated frontend form/action patterns into shared helpers and a reusable `FormActions` component without changing behavior.
- Moved repeated detail-grid styling into global frontend CSS and removed identical local route styles.
- Centralized frontend references parsing, optional-string payload helpers, and `?new=1` modal-opening checks.
- Simplified frontend markdown inline-token rendering by reusing a shared Svelte snippet.
- Added backend helpers for update-field application and taxonomy validation HTTP errors, replacing repeated assignment and exception blocks.
- Moved duplicated backend IP / forwarded-header parsing into a shared utility while preserving auth and health-check behavior.
- Collapsed repeated PDF / CSV / JSON report export internals into one private helper while keeping public routes unchanged.
- Switched attachment and report storage defaults from MinIO to SeaweedFS and renamed app-facing storage settings to `FINDINGS_OBJECT_STORAGE_*`.
- Added one-year object-lock retention for newly generated stored reports and exposed SHA256 plus lock/retention metadata in the report export API and session export table.
- Added file-based RS256 key configuration and mounted `./secrets` read-only into the backend for JWT keypair storage.
- Removed hardcoded runtime defaults for database connection details, JWT issuer / audience, session-hint cookie name, and other deployment-critical settings; these must now be supplied by `.env`.
- Standardized config defaults across code, Compose, `.env.example`, and `README.md` for proxy trust, ClamAV, object storage, OIDC, rate limits, and admin bootstrap settings.
- Defaulted ClamAV on in the Docker deployment path and block uploads with clear user-facing errors whenever scanning is disabled, unreachable, or unhealthy.
- Updated `/api/health` to include database, object storage, and OIDC capability status so the frontend can react to real dependency outages.
- Changed the frontend availability banner to slide the page down instead of overlaying the app.
- Removed the frontend OIDC route probe and now expose OIDC availability from backend startup state through `/api/health`.
- Added startup logging that reports which settings were missing from `.env`, supplied by Compose fallback, or supplied by Python defaults.

### Added
- Added an Alembic migration for report export integrity and retention metadata (`sha256`, `locked_until`, `retention_expires_at`).

### Fixed
- Neutralized spreadsheet-formula injection in CSV exports by prefixing dangerous user-controlled cell values before writing report rows.
- Fixed JWT verification so the backend accepts tokens for the configured primary signing mode instead of rejecting fresh logins when RS256 key files are present but HS256 remains active.
- Fixed proxy-aware rate limiting so deployments behind Caddy use the real client IP instead of collapsing requests onto the proxy address.
- Fixed OpenAPI type-generation CI by supplying dummy required environment variables to the backend schema-export workflow.
- Fixed blank optional integer env handling for `FINDINGS_REFRESH_SESSION_RETENTION_DAYS` so empty values are treated as unset instead of crashing settings validation.
- Fixed SeaweedFS startup / Compose integration issues in the default deployment path.

## [v0.1.18] - 2026-04-24

### Security
- Hardened attachment and report downloads against Content-Disposition header injection via filename. CRLF and control characters are stripped; non-ASCII filenames are emitted with both ASCII `filename=` and RFC 5987 `filename*=UTF-8''…` encoding.
- Blocked external-resource fetches during PDF report generation. Report markdown can no longer exfiltrate via `<img src="http://…">` or CSS `@import url(…)`; only inline `data:` URIs are permitted.
- Added magic-byte MIME validation for attachment uploads. Files whose first 16 bytes do not match the declared Content-Type are rejected with 415.
- Tightened Content-Security-Policy. Dropped `'unsafe-inline'` from `script-src`; SvelteKit now emits a hashed-script CSP via meta tag. Reduced the HTTP CSP header to `frame-ancestors 'none'`.
- Removed OIDC email-based account auto-linking. Unknown `(issuer, subject)` identities now always auto-provision a fresh user, eliminating the "nOAuth" risk when a customer IdP does not verify email ownership.
- Added per-username sliding-window login throttle that complements the existing per-IP limiter. Stops a distributed botnet from grinding a single account.
- Added 10-second clock-skew tolerance to JWT decoding to prevent spurious 401s on small server-time drift.
- Added size (≤ 4 KB serialized) and nesting-depth (≤ 4) caps on Client and Asset free-form `metadata_` fields.
- Added `iss` / `aud` / `iat` claims to issued JWTs with strict issuer and audience enforcement at decode time. **Breaking**: access tokens issued before the upgrade lack these claims and will be rejected; users silently re-refresh once on the first request after deploy.
- Added `umask 0077` to `backup/backup.sh` so backup archives are created mode 0600 and cannot be read by other users on a shared-UID host mount.

### Changed
- Added CPU and memory limits (`deploy.resources.limits`) to every service in `docker-compose.yml` to prevent one service from exhausting the host under load or a runaway scan.
- Extracted the inline `crypto.randomUUID` fallback polyfill from `app.html` to a static asset (`frontend/static/crypto-polyfill.js`) so it is covered by `script-src 'self'` under the new CSP.
- Updated stack version default to `0.1.18`.
- Centralized client-scope authorization in a single `ensure_client_access()` helper in `backend/app/api/deps.py` and refactored assets, sessions, attachments, and findings endpoints to use it, eliminating ad-hoc scope checks.
- Wrapped the blocking `ensure_buckets()` S3 bootstrap call in `asyncio.to_thread(...)` inside the FastAPI lifespan so startup no longer blocks the event loop.
- Wired `FINDINGS_ACCESS_TOKEN_EXPIRE_MINUTES`, `FINDINGS_REFRESH_TOKEN_EXPIRE_DAYS`, and `FINDINGS_MAILJET_FROM_NAME` through `docker-compose.yml` as explicit env passthroughs, and converted `MAILJET_*` vars to `${VAR:-default}` form.
- Removed unused frontend constants (`ASSET_TYPES`, `RISK_LEVELS`, `REMEDIATION_STATUSES`, `SESSION_STATUSES`) from `frontend/src/lib/api/{assets,findings,sessions}.ts`; taxonomy-driven lookups supersede them.

### Added
- Added a runbook for migrating JWT signing from HS256 to RS256 (generate keypair → dual-verify → wait access-token TTL → disable legacy HS256) to `README.md`.
- Added a one-shot backend test runner script (`backend/scripts/run-tests.sh`) that provisions the test database, copies tests into the backend container, runs `pytest`, and cleans up on exit.
- Added shared frontend DOM helpers (`frontend/src/lib/util/dom.ts`): `fieldId()` to replace per-page inline field-id generators across 10 Svelte routes, and `downloadBlob()` / `downloadResponseAsFile()` which dedupe the blob-download pattern across session report exports, stored export downloads, and attachment downloads.

## [v0.1.17] - 2026-04-23

### Changed
- Updated frontend toolchain dependencies and lockfile: TypeScript `6.0.3` and Vite `8.0.10`.
- Updated backend Python dependency pins: Uvicorn `0.46.0`, Pydantic `2.13.3`, Pydantic Settings `2.14.0`, bcrypt `5.0.0`, Authlib `1.7.0`, and python-json-logger `4.1.0`.
- Updated GitHub Actions versions in security workflows:
  - `actions/checkout` -> `v6`
  - `actions/setup-node` -> `v6`
  - `actions/setup-python` -> `v6`
  - `aquasecurity/trivy-action` -> `v0.36.0`
  - `github/codeql-action/upload-sarif` -> `v4`
- Updated Semgrep workflow action pin to the current `v1` target commit (`713efdd345f3035192eaa63f56867b88e63e4e5d`).
- Updated backup scheduler toolchain to Supercronic `0.2.45` with refreshed SHA1 verification values for `amd64` and `arm64`.
- Updated pinned container images in Compose for:
  - ClamAV `1.5.2` (immutable digest pin)
  - Gatus `v5.35.0` (immutable digest pin)

## [v0.1.16] - 2026-04-23

### Added
- Added OIDC canonical identity support with `users.oidc_issuer` + `users.oidc_subject` and Alembic migration `20260423_03`.
- Added OIDC state and nonce cookie checks in callback flow.
- Added redirect URI allowlist support for OIDC (`FINDINGS_OIDC_REDIRECT_URI_ALLOWLIST`).
- Added explicit CORS method/header settings (`FINDINGS_ALLOWED_METHODS`, `FINDINGS_ALLOWED_HEADERS`).
- Added backup encryption-at-rest support using a secret file path (`BACKUP_ENCRYPTION_SECRET_FILE`).
- Added supercronic fetch hardening script with SHA-verified install and optional local vendor cache.
- Added security audit workflow (`pip-audit`, production `npm audit`, Trivy image scan).
- Added backend async test harness scaffold in `backend/tests/`.
- Added hardened Caddy build context with `caddy-ratelimit` module.
- Added `.dockerignore` files for backend/frontend/backup contexts.
- Added `backend/scripts/export_openapi.py` and CI OpenAPI -> frontend type generation job.

### Changed
- Tightened frontend logout flow to await backend revocation, surface failure, and then clear local state deterministically.
- Reset taxonomy client state on logout/session clear.
- Replaced wildcard CORS settings in backend middleware with explicit allowlists.
- Changed default `FINDINGS_TRUST_PROXY_HEADERS` to `false` in backend config while keeping compose wiring explicit for proxy deployments.
- Replaced markdown `{@html}` rendering path with tokenized safe rendering in the frontend markdown viewer.
- Added global structured API error payload shape (`code`, `detail`, `timestamp`) via exception handlers while preserving `detail`.
- Aligned `/api/auth/refresh` failure responses with the structured error payload shape.
- Added SQLAlchemy engine disposal on backend shutdown.
- Switched attachment upload flow to stream through temporary file buffers (size-checked) instead of eager whole-file memory reads.
- Removed storage backend exception leakage from attachment API responses.
- Replaced mass assignment (`setattr` loops) with explicit field mapping in users/clients/assets/sessions/templates/findings update handlers.
- Added explicit transaction blocks for finding update history writes.
- Hardened containers with `cap_drop`/`no-new-privileges` defaults and read-only filesystems where configured.
- Pinned compose/runtime base images to immutable digests (Postgres, MinIO, ClamAV, Gatus, Python, Node, Caddy base images).
- Enforced stricter antivirus policy by runtime mode: production fails uploads when scanner is unavailable or misconfigured.
- Updated stack version default to `0.1.16`.

### Fixed
- Replaced silent `except Exception: pass` handling in findings and attachments flows with logged handling.
- Improved OIDC provisioning: identity is now issuer/subject first, with one-time email linking fallback.
- Fixed OIDC callback cookie binding to correctly read `oidc_state` and `oidc_nonce` cookies.

## [v0.1.15] - 2026-04-23

### Changed
- Kept session/security logging focused on public client IPs only (no location enrichment).
- Removed country display from profile session and security-activity UI.

### Removed
- Removed GeoIP country-enrichment support (`FINDINGS_GEOIP_DB_PATH`, backend GeoIP service, and `geoip2` dependency).
- Removed GeoIP Docker mount and related documentation/configuration entries.

## [v0.1.14] - 2026-04-23

### Added
- Added `auth_security_events` with Alembic migration `20260423_01`.
- Added security-event logging for refresh token reuse detection.
- Added `GET /api/auth/sessions`.
- Added `POST /api/auth/sessions/{refresh_session_id}/revoke`.
- Added `POST /api/auth/sessions/revoke-all`.
- Added `GET /api/auth/security-events`.
- Added profile UI sections for current sessions and security activity.
- Added per-session revoke controls in the profile page.
- Added logout-all-sessions control in the profile page.
- Added current-session highlighting in the profile page.
- Added `frontend/src/lib/api/auth.ts` for session and security endpoints.
- Added `scripts/redeploy.sh` for ordered rollout.
- Added `./scripts/first-run.sh redeploy`.
- Added backend health checks in Compose.
- Added `APP_VERSION` to `.env.example`.
- Added `FINDINGS_TRUST_PROXY_HEADERS` to control forwarded IP parsing behind reverse proxies.

### Changed
- Aligned backend runtime version and frontend UI version on one shared `APP_VERSION`.
- Wired Compose to pass `APP_VERSION` to backend as `FINDINGS_APP_VERSION`.
- Wired Compose to pass `APP_VERSION` to frontend build as `VITE_APP_VERSION`.
- Updated frontend version display to prefer `VITE_APP_VERSION`.
- Kept `frontend/package.json` as fallback for local frontend-only runs.
- Updated backend health response to include the active app version.
- Made `./scripts/first-run.sh up` use the ordered redeploy path.
- Gated frontend startup on backend health in Compose.
- Gated Caddy startup on backend health in Compose.
- Updated README deployment and configuration docs for version and redeploy flow.
- Hardened logout behavior in the frontend to clear browser-side state (`sessionStorage`, `localStorage`, and cache storage) in addition to auth state.
- Reset app-availability in-memory probe state on logout.
- Changed auth request IP capture to prefer forwarded proxy IPs (`X-Real-IP` / `X-Forwarded-For`) before container-local socket IPs.
- Changed revoke/logout security events to persist actor IP and User-Agent for better session activity visibility.
- Changed session-start backup behavior to run initial backup only if no successful backup exists in the last 24 hours.

### Fixed
- Escaped dynamic HTML values in email notifications.
- Sanitized email subjects before sending.
- Sanitized report HTML rendering for markdown and dynamic fields.
- Sanitized taxonomy color usage in report output.
- Fixed profile security activity showing `Unknown` IP/User-Agent for revoke-family and revoke-session events when actor metadata is available.

## [v0.1.13] - 2026-04-21

### Changed
- Removed Docker runtime mode switching. Startup now uses production behavior only.
- Removed `docker-compose.dev.yml` and mode-switch helper scripts.
- Updated backend and frontend Docker images to run production commands only.
- Removed `FINDINGS_RUNTIME_MODE` from compose wiring and `.env.example`.
- Updated README commands and deployment guidance to match prod-only operation.

## [v0.1.12] - 2026-04-17

### Changed
- Added bare-bones `Profile Settings` for authenticated users.
- Added `PATCH /api/users/me` for self-service profile updates.
- Added a bare-bones admin page for administrators.
- Added a sidebar user popup menu with profile, admin, and logout actions.

## [v0.1.11] - 2026-04-17

### Changed
- Expanded the baseline Alembic migration. Clean installs now create core application tables before later report-export and taxonomy revisions run.
- Added a shared frontend availability banner. It distinguishes backend/proxy/network outages from normal toast-level request failures.
- Added Docker runtime mode selection with `FINDINGS_RUNTIME_MODE`.
- Added `./scripts/first-run.sh mode <dev|prod>`.
- Added cleanup scripts for mode switches.
- Added `./scripts/first-run.sh retest`.
- Added `scripts/retest-sync.sh`.
- Added cache-only cleanup before pull for retest runs.
- Moved backend bind mounts to `docker-compose.dev.yml` only.
- Disabled Python bytecode file generation in the backend container.
- Kept backend Docker build context scoped to `./backend`.
- Updated the frontend app label to `VulnLedger`.
- Made the sidebar version label derive from `frontend/package.json`.

### Fixed
- Stopped the outage banner flow from replacing protected pages with a dead-end shell. Authenticated users now keep page state while the notice is shown.
- Split login-page startup checks. Whole-app availability no longer depends on the OIDC redirect endpoint. Only non-sensitive one-time probe results are cached.
- Added a frontend `crypto.randomUUID()` fallback for non-secure origins (for example HTTP LAN IP access).
- Updated availability polling to probe health even without an auth token so recovery clears stale outage banners.

## [v0.1.10] - 2026-04-16

### Changed
- Split MinIO storage. Evidence attachments and generated report artifacts now use separate buckets with new settings for bucket names and storage security.
- Added DB-managed versioned taxonomies for risk levels, remediation statuses, session statuses, and asset types. Added a seeded default taxonomy and admin APIs to create, list, and activate versions.
- Moved backend validation and report rendering to the active taxonomy version. Moved frontend badge/form/filter options there too.
- Added explicit report export guardrails for maximum finding count, maximum input size, and maximum generated output size.
- Added explicit attachment body-size controls in both the backend configuration and the Caddy reverse proxy configuration.

### Fixed
- Switched attachment downloads to stream from MinIO instead of buffering the entire object in backend memory.
- Stored generated PDF, CSV, and JSON report artifacts in the dedicated reports bucket during export.
- Added persistent report export records. Each record stores export date, file name, creator, object key, and taxonomy version. Added endpoints and UI support to list and download prior exports per session.
- Added schema-level length and count limits for large finding and session fields. Oversized content is now rejected before it can amplify report rendering cost.

## [v0.1.9] - 2026-04-16

### Changed
- Upgraded backend dependencies to current compatible releases. This includes FastAPI, Uvicorn, SQLAlchemy, Pydantic settings, Authlib, WeasyPrint `68.1`, and matching `pydyf`.
- Upgraded the frontend toolchain to the current compatible SvelteKit stack with Vite `8`, `@sveltejs/vite-plugin-svelte` `7`, and TypeScript `6`.
- Tightened several runtime image pins by moving Python, Node, Postgres, and MinIO to exact image tags instead of broader floating tags.

### Fixed
- Updated the backend settings loader to ignore unrelated Docker and host environment keys. Newer `pydantic-settings` versions now work cleanly with the shared `.env` file.

## [v0.1.8] - 2026-04-16

### Changed
- Added prerequisite-aware creation flows. Asset, session, and finding creation now redirect to the next required step when upstream data is missing.
- Added a top-level review-session creation flow on the sessions page. Wired the dashboard's New Client shortcut to open the create-client modal directly.
- Standardized non-critical frontend errors on a shared toast system. Positioned notifications in the bottom-right corner of the app.
- Added local Python `3.12` verification scaffolding via `.python-version`, `scripts/verify-backend.sh`, and a `verify-backend` command in `scripts/first-run.sh`.

### Fixed
- Fixed the session detail page loading issue when opening an individual review session. Added graceful toast fallbacks for session-detail load, save, and export failures.

## [v0.1.7] - 2026-04-16

### Fixed
- Stopped exposing backend and infrastructure details in website messages. Replaced 5xx and technical failures with generic user-facing frontend errors.

## [v0.1.6] - 2026-04-16

### Fixed
- Updated frontend auth error handling to tolerate non-JSON backend failures. Login and refresh issues now show a clean message.

## [v0.1.5] - 2026-04-16

### Changed
- Temporarily bound access and refresh tokens to the backend process in this release. This was later replaced by DB-backed refresh sessions.
- Enforced authenticated routing on every non-login page in the frontend and redirected signed-out users back to the login screen.
- Made logout await the server-side cookie deletion before clearing client auth state and redirecting to the login page.
- Protected the health endpoint behind the normal API authentication flow to keep non-auth API routes private.

## [v0.1.4] - 2026-04-16

### Changed
- Added optional Mailjet settings to `.env.example`. Documented the official Mailjet signup and quick-start links in the README.

## [v0.1.3] - 2026-04-16

### Changed
- Updated the README with the VulnLedger product name. Updated the canonical repository URL to `https://github.com/raymond-itsec/vulnledger.git`.

## [v0.1.2] - 2026-04-16

### Fixed
- Switched attachment downloads to authenticated fetch requests. Evidence files now download when the app keeps access tokens only in memory.
- Made session report exports reuse the authenticated request flow. Expired access tokens now refresh before PDF, CSV, and JSON exports.
- Added a reviewer listing endpoint for admins and reviewers. Added server-side reviewer validation. Creating review sessions no longer depends on manual user UUID entry.

## [v0.1.1] - 2026-04-16

### Fixed
- Switched password hashing to `bcrypt_sha256` with bcrypt fallback. Long initial admin passwords no longer fail during startup.
- Pinned `bcrypt` to `4.0.1`. `passlib==1.7.4` remains compatible during backend startup and admin seeding.

## [v0.1.0] - 2026-04-15

### Added
- Added a project changelog in Keep a Changelog format.
- Added a `.env.example` template for secure first-run configuration.
- Added `scripts/first-run.sh` to streamline first-time setup, preflight checks, log access, and reset flows.

### Changed
- Updated the Caddy deployment to use a hostname-based site address so Automatic HTTPS can activate when `CADDY_HOST` is set to a public domain.
- Pinned the Caddy container image to `caddy:2.11.2-alpine` for reproducible deployments.
- Exposed `443/udp` on the Caddy service so HTTP/3 can work alongside HTTPS.
- Hardened Docker Compose defaults. Moved secrets and initial admin bootstrap into environment variables. Bound internal service ports to `127.0.0.1`.
- Changed OIDC login to bootstrap sessions from the refresh cookie instead of putting access tokens in the URL.
- Made ClamAV uploads fail closed when scanning is configured but unavailable.

### Fixed
- Escaped markdown-rendered finding, session, and template content to prevent stored XSS in the frontend preview and detail views.
- Enforced client-scope authorization checks on attachment listing and downloads.
- Updated backend Docker image dependencies to use Debian's current `libgdk-pixbuf-2.0-0` package name. Builds now succeed on newer slim base images.
- Made Caddy host ports configurable with environment variables. Local conflicts on `80/443` can now be resolved without editing Compose files.
- Documented the recommended first-run and reset flow. Partial installs are easier to recover.
