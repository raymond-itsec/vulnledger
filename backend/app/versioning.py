"""Single source of truth for API version path constants.

Kept dependency-free (no router imports, no FastAPI imports, no
config imports) so any module in the backend can import these
constants without risking a circular import. Routers in
`app.main.API_VERSIONS` declare which versions exist and which is
current, but the *path string* derivations live here so that code
that needs to build a versioned URL or cookie path (auth cookies,
OIDC cookies, metric routes, redirect targets, ...) does not need
to reach into `app.main`.

If a future v2 cutover changes which version is `current`, update
the value of `CURRENT_API_VERSION` here AND flip the `current`
flag in `app.main.API_VERSIONS`. The two stay aligned by
convention; the test in `backend/tests/test_versioning.py`
asserts the alignment so they cannot drift silently.
"""

CURRENT_API_VERSION = "v1"
CURRENT_API_PREFIX = f"/api/{CURRENT_API_VERSION}"

# Cookies set before the /api/v1 URL migration were scoped to the
# unversioned `/api/auth` path. Browsers do not auto-evict cookies
# when the server stops using a path, so any cookie clearance code
# should also clear at this legacy path during the deprecation
# window. Drop after the LEGACY_API_SUNSET_DATE passes.
LEGACY_UNVERSIONED_API_PREFIX = "/api"
