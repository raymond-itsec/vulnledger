# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.5] - 2026-04-16

### Changed
- Bound access and refresh tokens to the current backend process so a backend redeploy invalidates all existing browser sessions.
- Enforced authenticated routing on every non-login page in the frontend and redirected signed-out users back to the login screen.
- Made logout await the server-side cookie deletion before clearing client auth state and redirecting to the login page.
- Protected the health endpoint behind the normal API authentication flow to keep non-auth API routes private.

## [v0.1.4] - 2026-04-16

### Changed
- Added the optional Mailjet settings to `.env.example` and documented the official Mailjet signup and quick-start links in the README.

## [v0.1.3] - 2026-04-16

### Changed
- Updated the README to use the VulnLedger product name and the canonical GitHub repository URL `https://github.com/raymond-itsec/vulnledger.git`.

## [v0.1.2] - 2026-04-16

### Fixed
- Switched attachment downloads to use authenticated fetch requests so evidence files still download when the app keeps the access token only in memory.
- Made session report exports reuse the authenticated request flow so expired access tokens refresh before PDF, CSV, and JSON exports.
- Added a reviewer listing endpoint for admins and reviewers, and validated reviewer selection server-side so creating review sessions no longer depends on manually entering a user UUID.

## [v0.1.1] - 2026-04-16

### Fixed
- Switched password hashing to `bcrypt_sha256` with bcrypt fallback so long initial admin passwords no longer fail during startup.
- Pinned `bcrypt` to `4.0.1` so `passlib==1.7.4` remains compatible during backend startup and admin seeding.

## [v0.1.0] - 2026-04-15

### Added
- Added a project changelog in Keep a Changelog format.
- Added a `.env.example` template for secure first-run configuration.
- Added `scripts/first-run.sh` to streamline first-time setup, preflight checks, log access, and reset flows.

### Changed
- Updated the Caddy deployment to use a hostname-based site address so Automatic HTTPS can activate when `CADDY_HOST` is set to a public domain.
- Pinned the Caddy container image to `caddy:2.11.2-alpine` for reproducible deployments.
- Exposed `443/udp` on the Caddy service so HTTP/3 can work alongside HTTPS.
- Hardened the Docker Compose defaults by moving secrets and the initial admin bootstrap into environment variables and binding internal service ports to `127.0.0.1`.
- Changed OIDC login to bootstrap sessions from the refresh cookie instead of putting access tokens in the URL.
- Made ClamAV uploads fail closed when scanning is configured but unavailable.

### Fixed
- Escaped markdown-rendered finding, session, and template content to prevent stored XSS in the frontend preview and detail views.
- Enforced client-scope authorization checks on attachment listing and downloads.
- Updated the backend Docker image dependencies to use Debian's current `libgdk-pixbuf-2.0-0` package name so builds succeed on newer slim base images.
- Made the Caddy host ports configurable via environment variables so local port conflicts on `80/443` can be resolved without editing Compose files.
- Documented the recommended first-run and reset flow so partial installs are easier to recover from.
