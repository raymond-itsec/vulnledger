import logging
from contextlib import asynccontextmanager
import ipaddress

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import attachments, auth, assets, clients, findings, reports, sessions, taxonomy, templates, users
from app.api.deps import get_current_user
from app.config import settings
from app.database import engine
from app.logging_config import configure_logging
from app.models.user import User
from app.schemas.error import make_error_payload
from app.services.seed import seed_admin_user, sync_builtin_templates
from app.services.storage import ensure_buckets
from app.services.taxonomy import ensure_default_taxonomy_version

configure_logging()

logger = logging.getLogger(__name__)

MIN_SECRET_KEY_BYTES = 32

_secret_key_bytes = len(settings.secret_key.encode("utf-8"))
if _secret_key_bytes < MIN_SECRET_KEY_BYTES:
    reason = (
        "FINDINGS_SECRET_KEY is not set"
        if _secret_key_bytes == 0
        else (
            f"FINDINGS_SECRET_KEY is too short: got {_secret_key_bytes} bytes, "
            f"require at least {MIN_SECRET_KEY_BYTES}"
        )
    )
    logger.critical(
        "Refusing to start: %s. Generate a strong value, e.g. "
        "`python -c 'import secrets; print(secrets.token_urlsafe(32))'`.",
        reason,
    )
    raise RuntimeError(reason)

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
        logger.warning("MinIO not available -- file attachments and report storage disabled")
    yield
    await engine.dispose()


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
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content=make_error_payload(
            code="rate_limited",
            detail="Too many requests. Please slow down.",
        ),
    )

app.state.limiter = limiter


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    code = detail.lower().replace(" ", "_").replace(".", "")[:64] or "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(code=code, detail=detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=make_error_payload(
            code="validation_error",
            detail="Request validation failed.",
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error at %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=make_error_payload(
            code="internal_error",
            detail="Internal server error.",
        ),
    )

# Middleware (order matters: outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
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


def _parse_ip_candidate(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    # Handle potential "IP:port" form from some proxies.
    if candidate.count(":") == 1 and "." in candidate:
        host, _, _ = candidate.partition(":")
        candidate = host.strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _extract_forwarded_ips(request: Request) -> list[str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if not forwarded_for:
        return []
    values: list[str] = []
    for part in forwarded_for.split(","):
        normalized = _parse_ip_candidate(part)
        if normalized:
            values.append(normalized)
    return values


def _effective_probe_ip(request: Request) -> str | None:
    """Resolve the probe source IP, preferring forwarded client IP over proxy IP."""
    if settings.trust_proxy_headers:
        forwarded_ips = _extract_forwarded_ips(request)
        if forwarded_ips:
            # X-Forwarded-For is client, proxy1, proxy2... -> left-most is origin.
            return forwarded_ips[0]
        x_real_ip = _parse_ip_candidate(request.headers.get("x-real-ip"))
        if x_real_ip:
            return x_real_ip
    return _parse_ip_candidate(request.client.host if request.client else None)


def _is_rfc1918_or_loopback(value: str | None) -> bool:
    parsed_value = _parse_ip_candidate(value)
    if not parsed_value:
        return False
    ip = ipaddress.ip_address(parsed_value)
    if ip.version == 4:
        return (
            ip in ipaddress.ip_network("10.0.0.0/8")
            or ip in ipaddress.ip_network("172.16.0.0/12")
            or ip in ipaddress.ip_network("192.168.0.0/16")
            or ip in ipaddress.ip_network("127.0.0.0/8")
        )
    return ip.is_loopback


@app.get("/api/health")
async def health(_: User = Depends(get_current_user)):
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/health/live")
async def health_live(request: Request):
    source_ip = _effective_probe_ip(request)
    if not _is_rfc1918_or_loopback(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Probe endpoint is restricted to internal networks.",
        )
    return {"status": "ok"}
