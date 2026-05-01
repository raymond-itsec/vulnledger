# Configuration

Application settings use the `FINDINGS_` prefix. The deployment also exposes supporting Docker, port, and Caddy variables through the same `.env` file.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_HOST` | See `.env.example` | PostgreSQL host used by the backend to build its connection string |
| `POSTGRES_SERVICE_PORT` | See `.env.example` | PostgreSQL container/service port used by the backend connection string |
| `POSTGRES_USER` | See `.env.example` | PostgreSQL username |
| `POSTGRES_PASSWORD` | See `.env.example` | PostgreSQL password |
| `POSTGRES_DB` | See `.env.example` | PostgreSQL database name |
| `FINDINGS_LOG_LEVEL` | `INFO` | Backend log verbosity (`DEBUG \| INFO \| WARNING \| ERROR \| CRITICAL`, case-insensitive). Invalid values refuse startup. |
| `FINDINGS_ACCESS_TOKEN_EXPIRE_MINUTES` | `5` | Access token lifetime |
| `FINDINGS_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Per-token refresh lifetime; each rotation issues a new token with this expiry (bounded by the family cap below) |
| `FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS` | `30` | **Security policy.** Absolute ceiling on a single login: no amount of rotation extends a refresh-token family past this. When crossed, the family is revoked and the user must log in again. Must be between `7` and `30` inclusive. |
| `FINDINGS_REFRESH_SESSION_RETENTION_DAYS` | _auto_ (`2 x FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS`) | **DB housekeeping.** How long already-dead refresh-session rows (expired or revoked) are kept in `auth_refresh_sessions` before the pruner deletes them. Must be `>= 2 x FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS`. Affects forensic/audit window only; has no effect on auth behavior. |
| `FINDINGS_TRUST_PROXY_HEADERS` | `true` | Trust proxy headers (for example from Caddy) to extract real client IPs |
| `FINDINGS_ALLOWED_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | CORS allowed origins |
| `FINDINGS_ALLOWED_METHODS` | `["GET","POST","PATCH","DELETE","OPTIONS"]` | CORS allowed methods |
| `FINDINGS_ALLOWED_HEADERS` | `["Authorization","Content-Type","Accept","If-None-Match"]` | CORS allowed request headers |
| `FINDINGS_OBJECT_STORAGE_ENDPOINT` | `seaweedfs:8333` | S3-compatible object-storage endpoint |
| `FINDINGS_OBJECT_STORAGE_ACCESS_KEY` | See `.env.example` | Required object-storage access key |
| `FINDINGS_OBJECT_STORAGE_SECRET_KEY` | See `.env.example` | Required object-storage secret key |
| `FINDINGS_OBJECT_STORAGE_SECURE` | `false` | Use HTTPS for object storage |
| `FINDINGS_OBJECT_STORAGE_EVIDENCE_BUCKET` | `finding-attachments` | Bucket for uploaded finding evidence |
| `FINDINGS_OBJECT_STORAGE_REPORTS_BUCKET` | `generated-reports` | Bucket for generated PDF/CSV/JSON exports |
| `FINDINGS_ATTACHMENT_MAX_FILE_SIZE_MB` | `25` | Authoritative attachment size limit enforced by the backend |
| `FINDINGS_PASSWORD_MIN_LENGTH` | `16` | Minimum password length. Hard floor: env values below 16 are rejected at startup. |
| `FINDINGS_PASSWORD_MAX_LENGTH` | `128` | Maximum password length. |
| `FINDINGS_PASSWORD_MIN_ZXCVBN_SCORE` | `3` | Minimum zxcvbn strength score (0-4). 3 is resistant to GPU-farm brute force for years. |
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
| `FINDINGS_INITIAL_ADMIN_USERNAME` | See `.env.example` | Required username for the seeded admin account |
| `FINDINGS_INITIAL_ADMIN_PASSWORD` | See `.env.example` | Required password for the seeded admin account |
| `FINDINGS_INITIAL_ADMIN_EMAIL` | See `.env.example` | Required email for the seeded admin account |
| `FINDINGS_INITIAL_ADMIN_FULL_NAME` | See `.env.example` | Required display name for the seeded admin account |
| `FINDINGS_CLAMAV_HOST` | `clamav` | ClamAV host; uploads are blocked whenever scanning is disabled or the scanner is unavailable |
| `FINDINGS_CLAMAV_PORT` | `3310` | ClamAV TCP port |
| `FINDINGS_JWT_ISSUER` | See `.env.example` | Expected JWT issuer claim |
| `FINDINGS_JWT_AUDIENCE` | See `.env.example` | Expected JWT audience claim |
| `FINDINGS_JWT_PRIVATE_KEY_PEM` | _(empty)_ | RS256 private key PEM (use this or `FINDINGS_JWT_PRIVATE_KEY_FILE`) |
| `FINDINGS_JWT_PUBLIC_KEY_PEM` | _(empty)_ | RS256 public key PEM (use this or `FINDINGS_JWT_PUBLIC_KEY_FILE`) |
| `FINDINGS_JWT_PRIVATE_KEY_FILE` | See `.env.example` | Path to an RS256 private key PEM file mounted in the backend container |
| `FINDINGS_JWT_PUBLIC_KEY_FILE` | See `.env.example` | Path to an RS256 public key PEM file mounted in the backend container |
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

## Sample `.env` for local development

```env
# Required
POSTGRES_USER=change_this_db_user
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DB=change_this_db_name
POSTGRES_HOST=localhost
POSTGRES_SERVICE_PORT=5432
FINDINGS_INITIAL_ADMIN_USERNAME=admin
FINDINGS_INITIAL_ADMIN_PASSWORD=change-this-admin-password
FINDINGS_INITIAL_ADMIN_EMAIL=admin@example.com
FINDINGS_INITIAL_ADMIN_FULL_NAME=Administrator

# SeaweedFS S3-compatible object storage
FINDINGS_OBJECT_STORAGE_ENDPOINT=localhost:8333
FINDINGS_OBJECT_STORAGE_ACCESS_KEY=findings-storage
FINDINGS_OBJECT_STORAGE_SECRET_KEY=change-this-object-storage-secret
FINDINGS_OBJECT_STORAGE_SECURE=false
FINDINGS_OBJECT_STORAGE_EVIDENCE_BUCKET=finding-attachments
FINDINGS_OBJECT_STORAGE_REPORTS_BUCKET=generated-reports
FINDINGS_REPORT_RETENTION_DAYS=365

# JWT signing (RS256)
FINDINGS_JWT_ISSUER=vulnledger-backend
FINDINGS_JWT_AUDIENCE=vulnledger-api
FINDINGS_JWT_PRIVATE_KEY_FILE=./secrets/jwt_private_key.pem
FINDINGS_JWT_PUBLIC_KEY_FILE=./secrets/jwt_public_key.pem

# Optional: Upload / report guardrails
# The backend value is the authoritative attachment limit.
# Keep the Caddy limit at or slightly above it so oversized uploads are rejected early.
FINDINGS_ATTACHMENT_MAX_FILE_SIZE_MB=25
FINDINGS_REPORT_MAX_FINDINGS=250
FINDINGS_REPORT_MAX_INPUT_CHARS=200000
FINDINGS_REPORT_MAX_OUTPUT_SIZE_MB=25

# Optional: Email notifications
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

# Optional: ClamAV
FINDINGS_CLAMAV_HOST=localhost
FINDINGS_CLAMAV_PORT=3310

# Optional: Reverse proxy upload cap (Caddy)
CADDY_ATTACHMENT_MAX_SIZE=30MB

# Optional: Unified app version shown in UI and backend metadata
APP_VERSION=0.2.0
```

## JWT signing (RS256)

Access tokens are signed and verified with RS256 only.

1. **Generate an RSA key pair** (keep the private key secret; 2048-bit RSA minimum):
   ```bash
   openssl genrsa -out jwt-private.pem 2048
   openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem
   ```
2. **Load the keys into the backend** using either mounted files or PEM env vars. The default Docker path is:
   ```bash
   FINDINGS_JWT_PRIVATE_KEY_FILE=/run/secrets/jwt_private_key.pem
   FINDINGS_JWT_PUBLIC_KEY_FILE=/run/secrets/jwt_public_key.pem
   ```
3. **Set stable issuer and audience values**:
   ```bash
   FINDINGS_JWT_ISSUER=vulnledger-backend
   FINDINGS_JWT_AUDIENCE=vulnledger-api
   ```

## Backup configuration

Set on the `backup` service (no `FINDINGS_` prefix):

| Variable | Default | Description |
|---|---|---|
| `BACKUP_CRON` | `0 2 * * *` | Cron schedule (default: daily 2 AM) |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep old backups |
| `BACKUP_ENCRYPTION_SECRET_FILE` | `/run/secrets/backup_encryption_passphrase` | Path to backup encryption passphrase file |
| `BACKUP_ENCRYPTION_REQUIRED` | `false` | Require passphrase file for every backup; forced in `production` runtime mode |
