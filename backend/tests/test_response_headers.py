"""Lock the backend response-header contract.

Security headers (X-Frame-Options, Referrer-Policy, Permissions-
Policy, Content-Security-Policy, etc.) are set by CADDY at the edge,
not by the backend. The backend used to set duplicates, sometimes
with conflicting values (Caddy's Permissions-Policy includes
clipboard-write=(self) for the copy buttons; backend's older copy
omitted it). De-duplicated 2026-05-05.

These tests assert two things:

1. The backend does NOT emit any of the security headers Caddy owns.
   Re-adding one would silently re-introduce duplicate headers in
   front of Caddy.

2. The backend DOES emit Cache-Control: no-store on /api/* responses.
   That's app-aware caching policy that travels with the code.

Tests use FastAPI's TestClient so the full middleware stack is
exercised, not just unit-level helpers. Module-skipped when the
TEST_DATABASE_URL is not set, matching conftest's gate for tests
that require the full app + Postgres stack (the lifespan startup
hook seeds taxonomy / admin / templates).
"""

import os

import pytest

# Module-level skip mirrors conftest.py's `db_session` gate. CI
# workflow backend-tests.yml sets TEST_DATABASE_URL alongside the
# full FINDINGS_* env. Local pytest runs without those skip cleanly.
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Requires TEST_DATABASE_URL + full FINDINGS_* env stack (backend CI provides both)",
)


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


@pytest.fixture(scope="module")
def client():
    # Import inside the fixture so the FINDINGS_* env vars + Postgres
    # are in place before app.config + app.main load. The TestClient
    # context manager runs the lifespan startup hook (DB seed,
    # taxonomy bootstrap, etc.) so middleware tests exercise the
    # exact stack that production hits.
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_backend_does_not_emit_caddy_owned_security_headers(client):
    """Hit a public health endpoint; assert no Caddy-owned headers leak."""
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


def test_backend_sets_cache_control_no_store_on_api_paths(client):
    """App-aware caching directive should still travel with backend code."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store", (
        "Backend should set Cache-Control: no-store on /api/* responses "
        "because the JSON / file streams are dynamic. Caddy does not "
        "set this; if the middleware drops it, browsers and intermediate "
        "caches may serve stale data."
    )


def test_backend_does_not_force_cache_control_on_non_api_paths(client):
    """The /api/* gate exists for a reason: only API paths should be
    locked to no-store. The CacheControlMiddleware predicate must not
    accidentally cover non-API paths."""
    response = client.get("/definitely-not-an-api-path")
    # Whatever the status (likely 404), the Cache-Control should NOT
    # have been set to no-store by our middleware.
    assert response.headers.get("Cache-Control") != "no-store", (
        "CacheControlMiddleware should only set no-store on /api/* "
        "paths. If a non-/api/ path is getting no-store, the predicate "
        "in CacheControlMiddleware.dispatch is too broad."
    )
