import logging
import os
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import ipaddress

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import attachments, auth, assets, clients, findings, reports, sessions, taxonomy, templates, users
from app.api.deps import get_current_user
from app.config import settings
from app.database import engine
from app.logging_config import configure_logging
from app.models.user import User
from app.schemas.error import make_error_payload
from app.services.antivirus import probe_scanner
from app.services.seed import seed_admin_user, sync_builtin_templates
from app.services.storage import (
    EVIDENCE_BUCKET_NAME,
    REPORTS_BUCKET_NAME,
    ensure_buckets,
    get_minio_client,
)
from app.services.taxonomy import ensure_default_taxonomy_version

configure_logging()

logger = logging.getLogger(__name__)

MIN_SECRET_KEY_BYTES = 32
APP_START_MONOTONIC = time.monotonic()

_secret_key_bytes = len(settings.secret_key.encode("utf-8"))
if _secret_key_bytes < MIN_SECRET_KEY_BYTES:
    if _secret_key_bytes == 0:
        reason = "missing"
    else:
        reason = f"too short; must be at least {MIN_SECRET_KEY_BYTES} bytes"
    raise RuntimeError(f"Refusing to start: invalid signing configuration ({reason}).")

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_api])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_default_taxonomy_version()
    await seed_admin_user()
    await sync_builtin_templates()
    try:
        await asyncio.to_thread(ensure_buckets)
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


async def _check_database_health() -> dict[str, object]:
    started = time.perf_counter()
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        logger.warning("Health debug database check failed (%s)", exc.__class__.__name__)
        return {
            "status": "down",
            "reason": "unreachable",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _check_minio_health_sync() -> dict[str, object]:
    client = get_minio_client()
    evidence_exists = client.bucket_exists(EVIDENCE_BUCKET_NAME)
    reports_exists = client.bucket_exists(REPORTS_BUCKET_NAME)
    return {
        "evidence_bucket_exists": evidence_exists,
        "reports_bucket_exists": reports_exists,
    }


async def _check_minio_health() -> dict[str, object]:
    started = time.perf_counter()
    try:
        details = await asyncio.to_thread(_check_minio_health_sync)
        status_value = (
            "ok"
            if details["evidence_bucket_exists"] and details["reports_bucket_exists"]
            else "degraded"
        )
        return {
            "status": status_value,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            **details,
        }
    except Exception as exc:
        logger.warning("Health debug MinIO check failed (%s)", exc.__class__.__name__)
        return {
            "status": "down",
            "reason": "unreachable",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


async def _check_clamav_health() -> dict[str, object]:
    started = time.perf_counter()
    status_value, reason = await asyncio.to_thread(probe_scanner)
    payload: dict[str, object] = {
        "status": status_value,
        "reason": reason,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    payload["configured"] = settings.clamav_host.strip() != ""
    return payload


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


@app.get("/api/health/debug")
async def health_debug(request: Request):
    source_ip = _effective_probe_ip(request)
    if not _is_rfc1918_or_loopback(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Probe endpoint is restricted to internal networks.",
        )

    database_check, minio_check, clamav_check = await asyncio.gather(
        _check_database_health(),
        _check_minio_health(),
        _check_clamav_health(),
    )

    critical_checks = (database_check, minio_check)
    critical_down = any(check.get("status") == "down" for check in critical_checks)
    degraded = any(check.get("status") in {"down", "degraded"} for check in (minio_check, clamav_check))

    overall_status = "down" if critical_down else ("degraded" if degraded else "ok")
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE if critical_down else status.HTTP_200_OK

    payload = {
        "status": overall_status,
        "service": "backend",
        "version": settings.app_version,
        "commit": os.getenv("APP_GIT_SHA", "unknown"),
        "runtime_mode": settings.runtime_mode,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.monotonic() - APP_START_MONOTONIC),
        "source_ip": source_ip or "unknown",
        "checks": {
            "database": database_check,
            "minio": minio_check,
            "clamav": clamav_check,
        },
    }
    return JSONResponse(status_code=http_status, content=payload)
