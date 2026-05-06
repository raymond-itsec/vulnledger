# Security

## Authentication & authorization

- **JWT tokens** - Short-lived access tokens (5 min) with refresh rotation
- **HttpOnly cookies** - Refresh tokens stored in secure, HttpOnly, SameSite=Strict cookies
- **Authenticated pages only** - Every frontend page except the login screen requires an authenticated session
- **DB-backed refresh sessions** - Active refresh-session families survive backend restarts
- **Refresh-token family lifetime cap** - Every login starts a token family with an immutable `family_expires_at`. Rotation never extends it, so a stolen refresh token cannot be rotated indefinitely. See `FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS` (security policy, default 30 days, bounded 7-30) versus `FINDINGS_REFRESH_SESSION_RETENTION_DAYS` (DB cleanup lag for dead rows, auto-derived as 2 × the family cap). The two settings govern different things and should not be confused.
- **Token-version kill switch** - Logout or refresh-family revocation immediately invalidates outstanding access tokens for that user
- **bcrypt-sha256 hashing** - Passwords pre-hashed with HMAC-SHA256 then bcrypted (no 72-byte truncation, full passphrase contributes to the digest)
- **Password policy** - Min length 16 (hard floor, env can't go lower), max 128, zxcvbn score >= 3. Configurable per [Configuration](configuration.md).
- **RBAC** - Three roles (admin / reviewer / client_user) with server-enforced permissions
- **Client scoping** - `client_user` role sees only data belonging to their linked client (row-level filtering at ORM level)

## HTTP security

- **Edge rate limiting** - 30 req/min on `/api/v1/auth/login` (strict bucket, brute-force protection), 1200 req/min on `/api/v1/*` (general bucket); enforced in Caddy. Both rules match the legacy unversioned `/api/...` paths via optional `(?:v1/)?` regex during the deprecation window
- **Malformed-path rejection** - Caddy rejects requests with `//`, `/./`, `/../`, `%2F`, `%5C`, or `%00` in the path with 400, before any handler runs
- **Forwarding-header sanitization** - 9 spoofable headers (X-Forwarded-For, X-Real-IP, etc.) blocked at the edge
- **Body-size cap** - 1MB default, 30MB on the `/api/v1/findings/<id>/attachments` endpoint (anchored regexp, exact match)
- **HTTP timeouts** - read_body 30s, read_header 10s, write 60s, idle 2m
- **Security headers** - CSP (`frame-ancestors 'none'`, `base-uri 'self'`, `form-action 'self'`), COOP, CORP, X-Frame-Options DENY, X-Content-Type-Options nosniff, X-Permitted-Cross-Domain-Policies none, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy
- **HSTS** - `max-age=63072000; includeSubDomains; preload` over HTTPS
- **CORS** - Configurable allowed origins
- **TLS** - Auto-provisioned via Caddy (Let's Encrypt) in production

## File security

- **Content-type validation** - Only allowed MIME types accepted (images, PDF, text, CSV, JSON, ZIP)
- **Size limits** - Attachment uploads are limited in both Caddy and the backend; the backend is authoritative, and the Caddy cap should be set at or slightly above it to reject oversized uploads early
- **Virus scanning** - ClamAV scans every upload before storage; uploads are blocked when the scanner is disabled or unavailable
- **Separated storage buckets** - Evidence and generated exports are stored in different object-storage buckets
- **Proxied downloads** - Evidence files and stored exports are served through the backend (object storage is not exposed to the internet)

## Reporting controls

- **Export guardrails** - The backend rejects oversized exports based on finding count, total input size, and generated output size
- **Stored export metadata** - Each export records the export date, file name, creating user, format, size, SHA256, lock expiry, and taxonomy version used at generation time
- **Historical taxonomy reference** - Stored exports are linked to the taxonomy version that was active when they were created

## Operational

- **No US Cloud Act dependencies** - Fully self-hosted, EU-friendly. Self-hosted fonts (Inter, JetBrains Mono) instead of Google Fonts. No third-party scripts on user-facing pages.
- **Encrypted backups** - Production runtime mode requires a passphrase file for backup encryption. The backup container fails fast (loud banner, exit code 78) if the secret is missing instead of silently looping.
- **Change audit trail** - Per-field history on all finding modifications
- **Dependency lock** - Backend (`requirements.lock.txt`) and frontend (`package-lock.json`) both pinned. Lock-sync check in CI prevents drift.
- **Container hardening** - Backup container runs with `cap_drop: ["ALL"]` and `security_opt: ["no-new-privileges:true"]`. Even root inside the container can't chown.

## Security findings register

Every security or behavior-affecting finding identified during internal audits is tracked in [`docs/SECURITY-FINDINGS.md`](https://github.com/raymond-itsec/vulnledger/blob/main/docs/SECURITY-FINDINGS.md) with a stable `VL-YYYY-NNN` ID, plus a corresponding GitHub issue.

To report a vulnerability, use the **Report a Vulnerability** button on the [Security tab](https://github.com/raymond-itsec/vulnledger/security/advisories) of the repository (Private Vulnerability Reporting is enabled). Email fallback per [SECURITY.md](https://github.com/raymond-itsec/vulnledger/security/policy).
