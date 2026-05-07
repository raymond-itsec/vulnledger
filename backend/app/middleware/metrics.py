"""Prometheus metrics: definitions, HTTP middleware, scrape helpers.

The `/api/{version}/metrics` endpoint is registered in `app.main` and
restricted to RFC1918 + loopback source IPs (same pattern as the
liveness probe). vmagent (lands with the future observability stack)
will scrape it from the docker network or via the WireGuard mesh.

Cardinality discipline: every label is bounded.
- `method`         ~7 HTTP verbs
- `path_template`  bounded by route count (~30-40), normalized to
                   `__not_matched__` for unrouted requests so 404 spam
                   does not explode cardinality
- `status`         ~10 status codes seen in practice
- `risk_level`     ~5 (critical/high/medium/low/info)
- `role`           3 (admin/reviewer/client_user)
- `is_active`      2 (true/false)
- `format`         3 (pdf/csv/json)
- `code`           bounded by HTTPException detail strings (~20-30)

Single-process mode: every metric lives in process memory and is
returned by `generate_latest()` on each scrape. When we run more than
one uvicorn worker per container, switch to `prometheus_client.multiprocess`
file-based aggregation.
"""
from __future__ import annotations

import sys
import time
from typing import Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ---------------------------------------------------------------------
# HTTP metrics
# ---------------------------------------------------------------------

HTTP_REQUESTS_TOTAL = Counter(
    "vl_http_requests_total",
    "Total HTTP requests by method, route template, and response status.",
    ["method", "path_template", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "vl_http_request_duration_seconds",
    "HTTP request duration in seconds, by method and route template.",
    ["method", "path_template"],
    # Default Prometheus buckets are biased toward sub-second responses,
    # which fits a JSON API. Buckets in seconds: 5ms .. 10s.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "vl_http_requests_in_progress",
    "In-flight HTTP requests by method.",
    ["method"],
)

HTTP_ERRORS_TOTAL = Counter(
    "vl_http_errors_total",
    "Total HTTP error responses by error code (from the canonical error envelope).",
    ["code"],
)

# ---------------------------------------------------------------------
# DB pool metrics (read on demand from SQLAlchemy on each scrape)
# ---------------------------------------------------------------------

DB_POOL_SIZE = Gauge(
    "vl_db_pool_size",
    "Configured SQLAlchemy connection pool size.",
)

DB_POOL_CHECKED_OUT = Gauge(
    "vl_db_pool_checked_out",
    "Connections currently checked out of the SQLAlchemy pool.",
)

DB_POOL_CHECKED_IN = Gauge(
    "vl_db_pool_checked_in",
    "Connections currently idle in the SQLAlchemy pool.",
)

# ---------------------------------------------------------------------
# Business metrics (computed via SELECT COUNT on each scrape; live in
# app.services.business_metrics)
# ---------------------------------------------------------------------

CLIENTS_COUNT = Gauge("vl_clients_count", "Total clients (customers).")
ASSETS_COUNT = Gauge("vl_assets_count", "Total reviewed assets.")
SESSIONS_COUNT = Gauge("vl_sessions_count", "Total review sessions.")
FINDINGS_COUNT = Gauge(
    "vl_findings_count",
    "Total findings by risk level.",
    ["risk_level"],
)
USERS_COUNT = Gauge(
    "vl_users_count",
    "Total users by role and active state.",
    ["role", "is_active"],
)
INVITES_PENDING_COUNT = Gauge(
    "vl_invites_pending_count",
    "Pending (unredeemed, unexpired) invites.",
)
ATTACHMENTS_COUNT = Gauge(
    "vl_attachments_count",
    "Total finding attachments.",
)
REPORT_EXPORTS_COUNT = Gauge(
    "vl_report_exports_count",
    "Total stored report exports by format.",
    ["format"],
)

# ---------------------------------------------------------------------
# ClamAV reachability (refreshed on each scrape; cheap PING over TCP)
# ---------------------------------------------------------------------

CLAMAV_UP = Gauge(
    "vl_clamav_up",
    "1 if the ClamAV daemon answered PING on the last scrape, 0 otherwise. "
    "Reads 0 when ClamAV is configured but unreachable; absent when not configured.",
)


def collect_clamav_metrics() -> None:
    """Update vl_clamav_up by probing the ClamAV daemon.

    Called from the /metrics handler on every scrape. probe_scanner()
    catches all exceptions internally and returns a state string, so a
    ClamAV outage cannot break the scrape.

    "disabled" leaves the gauge unset (absent in the scrape output) so
    operators can distinguish "not configured" from "configured + down"
    via PromQL `absent(vl_clamav_up)` vs `vl_clamav_up == 0`.
    """
    # Local import: services.antivirus pulls in app config which
    # imports a chain that ends back at metrics during startup.
    from app.services.antivirus import probe_scanner

    state, _detail = probe_scanner()
    if state == "ok":
        CLAMAV_UP.set(1)
    elif state == "down":
        CLAMAV_UP.set(0)
    # "disabled" -> leave unset; absent metric is the signal.


# ---------------------------------------------------------------------
# App info (set once at module load; always reads as 1)
# ---------------------------------------------------------------------

APP_INFO = Gauge(
    "vl_app_info",
    "App build info; the gauge value is always 1, the version + python_version live as labels.",
    ["version", "python_version"],
)


def init_app_info(app_version: str) -> None:
    """Stamp the app_info marker. Call once at startup."""
    APP_INFO.labels(
        version=app_version,
        python_version=sys.version.split()[0],
    ).set(1)


# ---------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------

UNMATCHED_PATH_TEMPLATE = "__not_matched__"


def _resolve_path_template(request: Request) -> str:
    """After call_next runs, the matched route is in `request.scope`.
    Use the route's path template (`/api/v1/findings/{id}`), not the
    raw URL path, to keep cardinality bounded.
    """
    route = request.scope.get("route")
    template: Optional[str] = getattr(route, "path", None) if route else None
    return template or UNMATCHED_PATH_TEMPLATE


class MetricsMiddleware(BaseHTTPMiddleware):
    """Per-request HTTP instrumentation.

    Emits `vl_http_requests_total`, `vl_http_request_duration_seconds`,
    and tracks in-flight requests via `vl_http_requests_in_progress`.

    Place innermost in the middleware stack so the route is resolved
    by the time we read `request.scope["route"]`.
    """

    async def dispatch(self, request: Request, call_next):
        method = request.method
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()

        duration = time.perf_counter() - start
        path_template = _resolve_path_template(request)
        status = str(response.status_code)
        HTTP_REQUESTS_TOTAL.labels(
            method=method, path_template=path_template, status=status
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method, path_template=path_template
        ).observe(duration)
        return response


# ---------------------------------------------------------------------
# Pool metrics collector (sync; called from /metrics handler)
# ---------------------------------------------------------------------


def collect_pool_metrics() -> None:
    """Update DB pool gauges from SQLAlchemy's pool. Cheap (in-memory
    counters); safe to call on every scrape.
    """
    # Local import to avoid a circular import at module load time.
    from app.database import engine

    pool = engine.pool
    # `pool.size()` returns the configured pool size for QueuePool;
    # `checkedout()` and `checkedin()` are real-time counters.
    DB_POOL_SIZE.set(pool.size())
    DB_POOL_CHECKED_OUT.set(pool.checkedout())
    DB_POOL_CHECKED_IN.set(pool.checkedin())


# ---------------------------------------------------------------------
# Scrape output
# ---------------------------------------------------------------------


def render_metrics() -> bytes:
    """Render the current metric values in Prometheus text exposition
    format. The /metrics endpoint should set Content-Type from the
    re-exported `CONTENT_TYPE_LATEST` constant.
    """
    return generate_latest()


__all__ = [
    "CONTENT_TYPE_LATEST",
    "MetricsMiddleware",
    "HTTP_ERRORS_TOTAL",
    "init_app_info",
    "collect_pool_metrics",
    "collect_clamav_metrics",
    "render_metrics",
]
