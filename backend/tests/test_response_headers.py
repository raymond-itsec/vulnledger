"""Lock the backend response-header contract.

Security headers (X-Frame-Options, Referrer-Policy, Permissions-
Policy, Content-Security-Policy, etc.) are set by CADDY at the edge,
not by the backend. The backend used to set duplicates, sometimes
with conflicting values (Caddy's Permissions-Policy includes
clipboard-write=(self) for the copy buttons; backend's older copy
omitted it). De-duplicated 2026-05-05.

These tests assert two things:

1. The backend's CacheControlMiddleware does NOT emit any of the
   security headers Caddy owns. Re-adding one would silently
   re-introduce duplicate headers in front of Caddy.

2. The middleware DOES emit Cache-Control: no-store on /api/*
   responses, but NOT on non-/api/ responses. That's app-aware
   caching policy that travels with the code.

Tests build a minimal FastAPI app with only the CacheControlMiddleware
applied, so they exercise the exact middleware logic without dragging
in the full app's lifespan startup (DB seeding, taxonomy bootstrap,
S3 buckets, etc.). That keeps the tests fast, self-contained, and
runnable without any FINDINGS_* / POSTGRES_* env stack.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import CacheControlMiddleware


# Headers the backend MUST NOT set (Caddy owns them all). If any of
# these starts appearing on a backend response again, the test fails
# loudly with the exact header name.
CADDY_OWNED_HEADERS = (
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
    "Content-Security-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "X-Permitted-Cross-Domain-Policies",
    "Strict-Transport-Security",
)


def _build_minimal_app() -> FastAPI:
    """Tiny FastAPI app with only the middleware-under-test wired up.

    Two routes mirror the predicate the middleware branches on so
    the tests can hit each side: a `/api/*` path (should get
    no-store) and a non-`/api/` path (should not).
    """
    app = FastAPI()
    app.add_middleware(CacheControlMiddleware)

    @app.get("/api/v1/health/live")
    async def api_route():
        return {"status": "ok"}

    @app.get("/some-non-api-path")
    async def non_api_route():
        return {"hello": "world"}

    return app


def test_backend_does_not_emit_caddy_owned_security_headers():
    """Hit an /api/* route; assert no Caddy-owned headers leak."""
    client = TestClient(_build_minimal_app())
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200

    leaked = [h for h in CADDY_OWNED_HEADERS if h in response.headers]
    assert not leaked, (
        f"Backend leaked Caddy-owned security header(s): {leaked}. "
        f"These are set by Caddy at the edge; setting them in the "
        f"backend produces duplicate response headers (sometimes with "
        f"conflicting values). Drop the offending header from "
        f"backend/app/main.py CacheControlMiddleware."
    )


def test_backend_sets_cache_control_no_store_on_api_paths():
    """App-aware caching directive should still travel with backend code."""
    client = TestClient(_build_minimal_app())
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store", (
        "Backend should set Cache-Control: no-store on /api/* responses "
        "because the JSON / file streams are dynamic. Caddy does not "
        "set this; if the middleware drops it, browsers and intermediate "
        "caches may serve stale data."
    )


def test_backend_does_not_force_cache_control_on_non_api_paths():
    """The /api/* gate exists for a reason: only API paths should be
    locked to no-store. The CacheControlMiddleware predicate must not
    accidentally cover non-API paths."""
    client = TestClient(_build_minimal_app())
    response = client.get("/some-non-api-path")
    assert response.status_code == 200
    # Whatever Cache-Control comes from FastAPI's defaults, it should
    # NOT have been set to no-store by our middleware.
    assert response.headers.get("Cache-Control") != "no-store", (
        "CacheControlMiddleware should only set no-store on /api/* "
        "paths. If a non-/api/ path is getting no-store, the predicate "
        "in CacheControlMiddleware.dispatch is too broad."
    )
