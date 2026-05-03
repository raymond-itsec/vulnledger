"""Lock the refresh_token cookie path contract.

The refresh-token cookie MUST be scoped to a path that the refresh
endpoint actually serves. RFC 6265 path matching is strict: a cookie
set at path /api/auth is NOT sent on requests to /api/v1/auth/refresh.

This regression sneaked in during Phase 1.4 (URL prefix migration to
/api/v1/) when the cookie path was not migrated alongside the routes.
Symptom: every refresh attempt 401s after ~5 minutes (the access
token TTL), forcing the user to log back in repeatedly.

The tests assert that the cookie paths derive from
`app.versioning.CURRENT_API_PREFIX` so a future v2 cutover only needs
to flip CURRENT_API_VERSION in one place; cookie paths and router
mounts then move together automatically.
"""

from fastapi import Response

from app.api.auth import (
    _clear_refresh_cookie,
    _set_refresh_cookie,
)
from app.versioning import CURRENT_API_PREFIX, LEGACY_UNVERSIONED_API_PREFIX


def _set_cookie_headers(response: Response) -> list[str]:
    """Pull every Set-Cookie value off the response, lower-cased."""
    return [h.decode().lower() for k, h in response.raw_headers if k == b"set-cookie"]


def test_set_refresh_cookie_uses_versioned_path():
    response = Response()
    _set_refresh_cookie(response, "test-token-value")

    headers = _set_cookie_headers(response)
    refresh_header = next(
        (h for h in headers if "refresh_token=test-token-value" in h),
        None,
    )
    assert refresh_header is not None, "refresh_token cookie was not set"

    # Path must be `<current-api-prefix>/auth`. Hardcoded "/api/v1/auth"
    # would silently miss a v2 cutover; deriving from the registry means
    # the test passes as long as the version constant is consistent.
    expected_path = f"{CURRENT_API_PREFIX.lower()}/auth"
    assert f"path={expected_path}" in refresh_header, (
        f"refresh_token cookie path must match the current API prefix; "
        f"got: {refresh_header}"
    )

    # Sanity: hardening attributes preserved.
    assert "httponly" in refresh_header
    assert "samesite=strict" in refresh_header


def test_clear_refresh_cookie_clears_both_current_and_legacy_paths():
    """When clearing the cookie, hit BOTH paths.

    Users who had a refresh_token cookie set at the legacy unversioned
    path before Phase 1.4 shipped need that phantom cookie cleaned up.
    Otherwise their browser keeps it sitting in the jar (browsers do
    not auto-expire cookies just because the server stopped using
    that path).
    """
    response = Response()
    _clear_refresh_cookie(response)

    headers = _set_cookie_headers(response)
    delete_headers = [h for h in headers if "refresh_token=" in h and "max-age=0" in h]

    paths = sorted(
        h.split("path=")[1].split(";")[0]
        for h in delete_headers
        if "path=" in h
    )
    expected = sorted([
        f"{CURRENT_API_PREFIX.lower()}/auth",
        f"{LEGACY_UNVERSIONED_API_PREFIX.lower()}/auth",
    ])
    assert paths == expected, (
        f"Expected delete-cookie at both legacy and current paths, got: {paths}"
    )
