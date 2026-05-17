import logging
import os
import re
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api import attachments, auth, assets, clients, findings, invites, onboarding, reports, sessions, taxonomy, templates, users
from app.config import settings, startup_config_source_report
from app.database import engine, get_db
from app.logging_config import configure_logging
from app.middleware.metrics import (
    CONTENT_TYPE_LATEST,
    HTTP_ERRORS_TOTAL,
    MetricsMiddleware,
    collect_clamav_metrics,
    collect_pool_metrics,
    init_app_info,
    render_metrics,
)
from app.middleware.request_id import RequestIDMiddleware
from app.services.business_metrics import collect_business_metrics
from app.schemas.error import COMMON_ERROR_RESPONSES, make_error_payload
from app.services.antivirus import probe_scanner
from app.services.seed import seed_admin_user, seed_synthetic_user, sync_builtin_templates
from app.services.storage import (
    EVIDENCE_BUCKET_NAME,
    REPORTS_BUCKET_NAME,
    ensure_buckets,
    get_object_storage_client,
)
from app.services.ip_utils import (
    extract_forwarded_ips,
    is_rfc1918_or_loopback,
    parse_ip_candidate,
    rate_limit_ip_key,
)
from app.services.taxonomy import ensure_default_taxonomy_version
from app.versioning import CURRENT_API_PREFIX

configure_logging()

logger = logging.getLogger(__name__)

_startup_config_sources = startup_config_source_report()
if _startup_config_sources["missing_from_env_file"]:
    logger.info(
        "Configuration variables missing from .env: %s",
        ", ".join(_startup_config_sources["missing_from_env_file"]),
    )
if _startup_config_sources["compose_fallback"]:
    logger.info(
        "Configuration variables provided by Compose fallback: %s",
        ", ".join(_startup_config_sources["compose_fallback"]),
    )
if _startup_config_sources["python_default"]:
    logger.info(
        "Configuration variables provided by Python defaults: %s",
        ", ".join(_startup_config_sources["python_default"]),
    )

APP_START_MONOTONIC = time.monotonic()

# Rate limiter
limiter = Limiter(
    key_func=lambda request: rate_limit_ip_key(request, settings.trust_proxy_headers),
    default_limits=[settings.rate_limit_api],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_default_taxonomy_version()
    await seed_admin_user()
    await seed_synthetic_user()
    await sync_builtin_templates()
    try:
        await asyncio.to_thread(ensure_buckets)
    except Exception:
        logger.warning("Object storage not available -- file attachments and report storage disabled")
    yield
    await engine.dispose()


# API URL versioning registry. Single source of truth for which API
# versions exist, which one is current, and which are deprecated. Every
# version's `routers` list is mounted under `/api/<version>/`. The
# `LegacyApiRedirectMiddleware` redirects unversioned `/api/...` requests
# to whatever is marked `current`. The `DeprecatedVersionHeadersMiddleware`
# stamps `Deprecation: true` + `Sunset` headers on every response from a
# deprecated version's prefix, so external clients get programmatic
# notice both via the legacy redirect AND via direct calls to the
# deprecated version itself.
#
# To deprecate v1 once v2 ships:
#   API_VERSIONS["v1"]["current"] = False
#   API_VERSIONS["v1"]["sunset"]  = "Mon, DD MMM YYYY 00:00:00 GMT"
#   API_VERSIONS["v2"] = {"current": True, "sunset": None, "routers": [...]}
# After the v1 sunset date passes, the v1 entry can be removed entirely.
LEGACY_API_SUNSET_DATE = "Mon, 01 Jun 2026 00:00:00 GMT"

API_VERSIONS: dict[str, dict] = {
    "v1": {
        "current": True,
        "sunset": None,
        "routers": [
            auth.router,
            invites.router,
            onboarding.router,
            users.router,
            clients.router,
            assets.router,
            sessions.router,
            findings.router,
            templates.router,
            taxonomy.router,
            attachments.router,
            reports.router,
        ],
    },
}


def current_api_version() -> str:
    """Return the version key currently marked `current` in the registry."""
    for version, meta in API_VERSIONS.items():
        if meta.get("current"):
            return version
    raise RuntimeError("No API version marked current in API_VERSIONS")


# Sanity: the value imported from app.versioning at module load (above)
# must match the version the runtime registry marks current. Drift
# here would mean cookie paths and router mounts disagree silently, as
# happened during the /api/v1 URL migration before this module split.
# Failing at startup is loud; failing as a silent 401 hours later is not.
if CURRENT_API_PREFIX != f"/api/{current_api_version()}":
    raise RuntimeError(
        f"API version mismatch: app.versioning.CURRENT_API_PREFIX is "
        f"{CURRENT_API_PREFIX!r} but the registry's current version "
        f"resolves to /api/{current_api_version()}. Update both to match."
    )

# Matches `/api/vN` and `/api/vN/...` for any positive integer N. Used by
# the legacy redirect to recognize "this path is already version-prefixed,
# do not redirect even if N is unknown to the registry" (unknown versions
# fall through to FastAPI's natural 404).
VERSION_SEGMENT_RE = re.compile(r"^/api/v\d+(/|$)")


class LegacyApiRedirectMiddleware(BaseHTTPMiddleware):
    """308 redirect any unversioned `/api/...` request to the current
    versioned prefix. Preserves method + body (unlike 301). Adds
    `Deprecation: true` and `Sunset` headers so external callers get
    programmatic notice. The frontend SPA calls the current prefix
    directly; this redirect exists for transition support only.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and not VERSION_SEGMENT_RE.match(path):
            # Strip the bare "/api" prefix and prepend the current versioned
            # prefix. Example: "/api/users" -> "/api/v1/users".
            new_path = CURRENT_API_PREFIX + path[len("/api"):]
            location = new_path
            if request.url.query:
                location = f"{new_path}?{request.url.query}"
            return Response(
                status_code=308,
                headers={
                    "Location": location,
                    "Deprecation": "true",
                    "Sunset": LEGACY_API_SUNSET_DATE,
                },
            )
        return await call_next(request)


class DeprecatedVersionHeadersMiddleware(BaseHTTPMiddleware):
    """Stamp `Deprecation: true` + `Sunset` headers on every response
    served from a deprecated API version's prefix (i.e. any version where
    `current` is False and a `sunset` date is set). Today no version is
    deprecated, so this middleware is a no-op. When v1 gets deprecated
    after v2 ships, requests to `/api/v1/...` automatically receive the
    headers without further code changes.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        for version, meta in API_VERSIONS.items():
            if meta.get("current"):
                continue
            sunset = meta.get("sunset")
            if not sunset:
                continue
            if path.startswith(f"/api/{version}/") or path == f"/api/{version}":
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = sunset
                break
        return response


# Backend response-policy middleware.
#
# Security headers (X-Content-Type-Options, X-Frame-Options,
# Referrer-Policy, Permissions-Policy, Content-Security-Policy,
# Cross-Origin-Opener-Policy, Cross-Origin-Resource-Policy,
# X-Permitted-Cross-Domain-Policies, Strict-Transport-Security) are
# OWNED BY CADDY at the edge (see Caddyfile `header { ... }` block).
# The backend used to set its own copies, which produced duplicate
# response headers (sometimes with conflicting values, e.g. our
# Permissions-Policy needs `clipboard-write=(self)` for the copy
# buttons but the backend version omitted it). Caddy now wins; this
# middleware only sets directives that are app-aware.
#
# Cache-Control on /api/*: backend KNOWS its responses are dynamic
# JSON / file streams and should never be cached. Keeping this here
# rather than in Caddy means it travels with the app code and
# applies even if the deployment topology changes (Caddy bypassed,
# different edge proxy, etc.).
#
# X-XSS-Protection was also dropped: deprecated and ignored by every
# modern browser since 2020 (Chrome removed the auditor entirely;
# Firefox / Safari never implemented it). Caddy doesn't set it
# either - it would be misleading to leave a header that does nothing.
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


app = FastAPI(
    title="Security Findings Manager",
    version=settings.app_version,
    lifespan=lifespan,
    # OpenAPI schema + interactive docs live under the current API URL
    # prefix so they are versioned alongside the routes they describe and
    # reachable via the same Caddy `/api/*` reverse-proxy rule. When v2
    # becomes current via API_VERSIONS, these paths flip automatically.
    # Swagger UI and ReDoc each toggle off by setting their URL to None
    # (per FastAPI convention).
    openapi_url=f"{CURRENT_API_PREFIX}/openapi.json",
    docs_url=f"{CURRENT_API_PREFIX}/docs" if settings.swagger_ui_enabled else None,
    redoc_url=f"{CURRENT_API_PREFIX}/redoc" if settings.redoc_enabled else None,
)

# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    HTTP_ERRORS_TOTAL.labels(code="rate_limited").inc()
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
    HTTP_ERRORS_TOTAL.labels(code=code).inc()
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(code=code, detail=detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Surface per-field validation issues in the structured `details`
    # field so the frontend can highlight the offending fields without
    # parsing free-form text. Each item is Pydantic's standard error
    # dict: `{"loc": ["body", "field"], "msg": "...", "type": "..."}`.
    HTTP_ERRORS_TOTAL.labels(code="validation_error").inc()
    return JSONResponse(
        status_code=422,
        content=make_error_payload(
            code="validation_error",
            detail="Request validation failed.",
            details={"errors": exc.errors()},
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error at %s", request.url.path)
    HTTP_ERRORS_TOTAL.labels(code="internal_error").inc()
    return JSONResponse(
        status_code=500,
        content=make_error_payload(
            code="internal_error",
            detail="Internal server error.",
        ),
    )

# Middleware. Starlette's `add_middleware` prepends, so the LAST added
# is the OUTERMOST in the request flow. Adding in this order makes
# RequestID outermost (so its contextvars are set before any other
# middleware or handler runs and every log record can pick them up),
# then CacheControl, CORS, DeprecatedVersionHeaders, Legacy. The 308
# short-circuit response from Legacy still picks up CORS, the
# Cache-Control on /api/*, AND the X-Request-ID / X-VL-Request-ID
# headers on the way back out. Security headers are set by Caddy at
# the edge - see the comment on CacheControlMiddleware above.
app.add_middleware(MetricsMiddleware)  # innermost: route is resolved by the time it reads request.scope["route"]
app.add_middleware(LegacyApiRedirectMiddleware)
app.add_middleware(DeprecatedVersionHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(RequestIDMiddleware)

# Stamp app_info gauge once at startup so it appears in every scrape.
init_app_info(settings.app_version)

# Mount every router from the API_VERSIONS registry under its version
# prefix. Adding a new version is a registry change; the loop picks it up.
# COMMON_ERROR_RESPONSES wires the canonical error envelope into the
# OpenAPI schema for every documented status (400, 401, 403, 404, 409,
# 422, 429, 500) so consumers reading the spec see the actual error
# shape, not just a generic Pydantic validation error.
for _version, _meta in API_VERSIONS.items():
    _prefix = f"/api/{_version}"
    for _router in _meta["routers"]:
        app.include_router(_router, prefix=_prefix, responses=COMMON_ERROR_RESPONSES)

# OIDC router is conditional on configuration. Today it lives under the
# current version only; if v2 ships and OIDC routes change, add the v2
# variant to API_VERSIONS["v2"]["routers"] and remove this conditional
# block.
if settings.oidc_enabled:
    from app.api import oidc
    app.include_router(oidc.router, prefix=CURRENT_API_PREFIX, responses=COMMON_ERROR_RESPONSES)


def _effective_probe_ip(request: Request) -> str | None:
    """Resolve the probe source IP, preferring forwarded client IP over proxy IP."""
    if settings.trust_proxy_headers:
        forwarded_ips = extract_forwarded_ips(request)
        if forwarded_ips:
            # X-Forwarded-For is client, proxy1, proxy2... -> left-most is origin.
            return forwarded_ips[0]
        x_real_ip = parse_ip_candidate(request.headers.get("x-real-ip"))
        if x_real_ip:
            return x_real_ip
    return parse_ip_candidate(request.client.host if request.client else None)


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


def _check_object_storage_health_sync() -> dict[str, object]:
    client = get_object_storage_client()
    evidence_exists = client.bucket_exists(EVIDENCE_BUCKET_NAME)
    reports_exists = client.bucket_exists(REPORTS_BUCKET_NAME)
    return {
        "evidence_bucket_exists": evidence_exists,
        "reports_bucket_exists": reports_exists,
    }


async def _check_object_storage_health() -> dict[str, object]:
    started = time.perf_counter()
    try:
        details = await asyncio.to_thread(_check_object_storage_health_sync)
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
        logger.warning("Health debug object storage check failed (%s)", exc.__class__.__name__)
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


@app.get("/api/v1/health")
async def health():
    database_check, object_storage_check = await asyncio.gather(
        _check_database_health(),
        _check_object_storage_health(),
    )

    critical_checks = (database_check, object_storage_check)
    critical_down = any(check.get("status") == "down" for check in critical_checks)
    degraded = any(check.get("status") == "degraded" for check in critical_checks)

    overall_status = "down" if critical_down else ("degraded" if degraded else "ok")
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE if critical_down else status.HTTP_200_OK

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall_status,
            "version": settings.app_version,
            "features": {
                "oidc_enabled": settings.oidc_enabled,
            },
            "checks": {
                "database": database_check,
                "object_storage": object_storage_check,
            },
        },
    )


@app.get("/api/v1/health/live")
async def health_live(request: Request):
    source_ip = _effective_probe_ip(request)
    if not is_rfc1918_or_loopback(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Probe endpoint is restricted to internal networks.",
        )
    return {"status": "ok"}


@app.get(f"{CURRENT_API_PREFIX}/metrics")
async def metrics_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Prometheus scrape target. Restricted to RFC1918 + loopback source
    IPs (same pattern as the liveness probe). vmagent will scrape this
    when the future observability stack lands. Path follows
    `CURRENT_API_PREFIX` so it auto-versions when v2 launches; vmagent
    scrape config will need updating at that cutover (see
    api_v2_launch_checklist.md).
    """
    source_ip = _effective_probe_ip(request)
    if not is_rfc1918_or_loopback(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Metrics endpoint is restricted to internal networks.",
        )

    # Pull live values into the gauges, then render. The HTTP and error
    # counters/histograms are updated by middleware/handlers throughout
    # the request lifecycle and are already current.
    collect_pool_metrics()
    collect_clamav_metrics()
    await collect_business_metrics(db)

    return Response(content=render_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/health/debug")
async def health_debug(request: Request):
    source_ip = _effective_probe_ip(request)
    if not is_rfc1918_or_loopback(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Probe endpoint is restricted to internal networks.",
        )

    database_check, object_storage_check, clamav_check = await asyncio.gather(
        _check_database_health(),
        _check_object_storage_health(),
        _check_clamav_health(),
    )

    critical_checks = (database_check, object_storage_check)
    critical_down = any(check.get("status") == "down" for check in critical_checks)
    degraded = any(
        check.get("status") in {"down", "degraded"}
        for check in (object_storage_check, clamav_check)
    )

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
            "object_storage": object_storage_check,
            "clamav": clamav_check,
        },
    }
    return JSONResponse(status_code=http_status, content=payload)
