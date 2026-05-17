# Quickstart

Get a local VulnLedger instance running in about five minutes.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) v2+
- [Node.js](https://nodejs.org/) 22+ (only if you plan to do frontend development)
- [Python](https://www.python.org/) 3.14+ (only if you plan to do backend development)

## Quick Start (Docker, recommended)

```bash
# 1. Clone the repository
git clone https://github.com/raymond-itsec/vulnledger.git vulnledger
cd vulnledger

# 2. Create your local environment file
./scripts/first-run.sh init

# 3. Review the secrets and initial admin values in .env
#    Optional: configure Mailjet if you want email notifications
#    Register: https://www.mailjet.com/pricing/
#    Quick start: https://documentation.mailjet.com/hc/en-us/articles/37251169295003--Quick-Start-with-Mailjet

# 4. Run the preflight checks
./scripts/first-run.sh doctor

# 5. Start all services
./scripts/first-run.sh up

# 6. Open in browser
open http://localhost
```

That's it. The app is now available at `http://localhost` with:

- Your configured initial admin account from `.env`
- 25 finding templates auto-synced on startup
- PostgreSQL, SeaweedFS, and all services running

## First-Run Helper

The repository includes a helper script for smoother installs:

```bash
./scripts/first-run.sh init             # create .env from .env.example
./scripts/first-run.sh doctor           # validate ports, secrets, and common setup issues
./scripts/first-run.sh redeploy         # ff-only pull + ordered rollout: migrate DB, backend, frontend
./scripts/first-run.sh verify-backend   # local Python 3.14 backend smoke-check
./scripts/first-run.sh up               # ordered rollout (same as redeploy)
./scripts/first-run.sh logs             # follow caddy, frontend, and backend logs
./scripts/first-run.sh down             # stop the stack
./scripts/first-run.sh reset            # stop the stack and remove named volumes
```

`doctor` catches two common setup problems before Docker starts:

- Host ports that are already in use
- Placeholder secrets that were never updated in `.env`

`scripts/first-run.sh` always uses production containers from `docker-compose.yml`. The backend image build context is `./backend`.

`redeploy` starts with `git pull --ff-only` (and exits if tracked git changes are present), then enforces rollout order: DB migrations first, backend second (waits for backend readiness), then frontend and Caddy last.

`reset` is the safest retry path after a failed first install if you changed `POSTGRES_PASSWORD` - PostgreSQL only applies that password when initializing a fresh data directory.

## Generating frontend types from the OpenAPI schema

If you change the backend API, regenerate the typed frontend client:

```bash
PYTHONPATH=backend \
  FINDINGS_JWT_PRIVATE_KEY_FILE=./secrets/jwt_private_key.pem \
  FINDINGS_JWT_PUBLIC_KEY_FILE=./secrets/jwt_public_key.pem \
  python backend/scripts/export_openapi.py backend/openapi.generated.json
npm --prefix frontend run generate:types
```

## Local Development (optional)

If you want hot reload on both frontend and backend:

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
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

!!! note "WeasyPrint system dependencies (required for PDF generation)"
    - **macOS:** `brew install pango libffi cairo glib`
    - **Ubuntu/Debian:** `apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2`
    - **Docker:** Already handled in the Dockerfile

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies `/api/*` to the backend.

### Supporting services only

You can run just the infrastructure services via Docker while developing locally:

```bash
# Start only PostgreSQL and SeaweedFS
docker compose up -d db seaweedfs

# Optional: Start ClamAV for virus scanning
docker compose up -d clamav
```

## Next steps

- Going to production? See [Deployment](deployment.md).
- Need to tune something? Every env var is documented in [Configuration](configuration.md).
- Want a backup strategy? [Operations](operations.md) covers backups, restores, and monitoring.
