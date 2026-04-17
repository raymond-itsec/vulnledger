import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import attachments, auth, assets, clients, findings, reports, sessions, taxonomy, templates, users
from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.services.seed import seed_admin_user, sync_builtin_templates
from app.services.storage import ensure_buckets
from app.services.taxonomy import ensure_default_taxonomy_version

logger = logging.getLogger(__name__)

if not settings.secret_key:
    raise RuntimeError("FINDINGS_SECRET_KEY must be set before starting the backend")

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_api])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_default_taxonomy_version()
    await seed_admin_user()
    await sync_builtin_templates()
    try:
        ensure_buckets()
    except Exception:
        logger.warning("MinIO not available — file attachments and report storage disabled")
    yield


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        return response


app = FastAPI(
    title="Security Findings Manager",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )

app.state.limiter = limiter

# Middleware (order matters: outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(findings.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# OIDC router (only if configured)
if settings.oidc_enabled:
    from app.api import oidc
    app.include_router(oidc.router, prefix="/api")


@app.get("/api/health")
async def health(_: User = Depends(get_current_user)):
    return {"status": "ok"}
