"""Lock the onboarding cookie path contract (VL-2026-018).

The onboarding cookie MUST be scoped to a path that the onboarding
endpoints actually serve. RFC 6265 path matching is strict: a cookie
set at path /api/onboarding is NOT sent on requests to
/api/v1/onboarding/state, so the verify-invite -> state -> complete
flow returned 401 on every call after the first.

This is the same regression class as the refresh-token cookie path
bug (see test_auth_cookie_paths.py). One file got missed during the
/api/v1 URL migration.

The tests assert that the cookie paths derive from
`app.versioning.CURRENT_API_PREFIX` so a future v2 cutover only
needs to flip CURRENT_API_VERSION in one place; cookie paths and
router mounts then move together automatically.
"""

from fastapi import Response

from app.api.onboarding import (
    _clear_onboarding_cookie,
    _set_onboarding_cookie,
)
from app.services.onboarding import ONBOARDING_COOKIE_NAME
from app.versioning import CURRENT_API_PREFIX, LEGACY_UNVERSIONED_API_PREFIX


def _set_cookie_headers(response: Response) -> list[str]:
    """Pull every Set-Cookie value off the response, lower-cased."""
    return [h.decode().lower() for k, h in response.raw_headers if k == b"set-cookie"]


def test_set_onboarding_cookie_uses_versioned_path():
    response = Response()
    _set_onboarding_cookie(response, "test-token-value")

    headers = _set_cookie_headers(response)
    cookie_header = next(
        (h for h in headers if f"{ONBOARDING_COOKIE_NAME.lower()}=test-token-value" in h),
        None,
    )
    assert cookie_header is not None, f"{ONBOARDING_COOKIE_NAME} cookie was not set"

    # Path must be `<current-api-prefix>/onboarding`. Hardcoded
    # "/api/onboarding" (the bug this test guards against) silently
    # misses every browser under RFC 6265 strict path-matching when
    # the routes mount at /api/v1/onboarding/*.
    expected_path = f"{CURRENT_API_PREFIX.lower()}/onboarding"
    assert f"path={expected_path}" in cookie_header, (
        f"{ONBOARDING_COOKIE_NAME} cookie path must match the current "
        f"API prefix; got: {cookie_header}"
    )

    # Sanity: hardening attributes preserved.
    assert "httponly" in cookie_header
    assert "samesite=strict" in cookie_header


def test_clear_onboarding_cookie_clears_both_current_and_legacy_paths():
    """When clearing the cookie, hit BOTH paths.

    Users who had an onboarding cookie set at the legacy unversioned
    path (or at the buggy hardcoded /api/onboarding path that predates
    the VL-2026-018 fix) need that phantom cookie cleaned up. Browsers
    do not auto-expire cookies just because the server stopped using
    that path.
    """
    response = Response()
    _clear_onboarding_cookie(response)

    headers = _set_cookie_headers(response)
    delete_headers = [
        h for h in headers
        if f"{ONBOARDING_COOKIE_NAME.lower()}=" in h and "max-age=0" in h
    ]

    paths = sorted(
        h.split("path=")[1].split(";")[0]
        for h in delete_headers
        if "path=" in h
    )
    expected = sorted([
        f"{CURRENT_API_PREFIX.lower()}/onboarding",
        f"{LEGACY_UNVERSIONED_API_PREFIX.lower()}/onboarding",
    ])
    assert paths == expected, (
        f"Expected delete-cookie at both legacy and current paths, got: {paths}"
    )
