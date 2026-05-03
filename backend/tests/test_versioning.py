"""Lock the alignment between app.versioning and app.main.API_VERSIONS.

The single source of truth for the *string* path is
`app.versioning.CURRENT_API_PREFIX`. The single source of truth for
*which routers exist under which version* is
`app.main.API_VERSIONS`. The two MUST agree on which version is
current. This test fails loudly if they ever drift.

(There is also a runtime check in `app.main` that raises at startup
on mismatch, but the test catches it during CI before deploy.)
"""

from app.main import current_api_version
from app.versioning import CURRENT_API_PREFIX, CURRENT_API_VERSION


def test_versioning_constants_agree_with_registry():
    assert CURRENT_API_PREFIX == f"/api/{current_api_version()}", (
        f"app.versioning.CURRENT_API_PREFIX is {CURRENT_API_PREFIX!r} but "
        f"the runtime registry resolves the current version to "
        f"/api/{current_api_version()}. Update one to match the other."
    )
    assert CURRENT_API_VERSION == current_api_version(), (
        f"app.versioning.CURRENT_API_VERSION is {CURRENT_API_VERSION!r} but "
        f"the runtime registry's current version is "
        f"{current_api_version()!r}. Update one to match the other."
    )
