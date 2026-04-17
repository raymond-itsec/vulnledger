# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Fixed
- Stopped the outage banner flow from replacing protected pages with a dead-end shell. Authenticated users now keep page state while the notice is shown.
- Split login-page startup checks. Whole-app availability no longer depends on the OIDC redirect endpoint. Only non-sensitive one-time probe results are cached.

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
- Bound access and refresh tokens to the current backend process. A backend redeploy now invalidates existing browser sessions.
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
