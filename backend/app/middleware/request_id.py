"""Per-request correlation IDs.

Two distinct identifiers per HTTP request, never conflated.

`X-Request-ID` (external / upstream lineage)
    Honored only when an incoming `X-Request-ID` header is present AND parses
    as a valid UUID. We never invent one ourselves: if upstream did not send
    a valid value, the response carries no `X-Request-ID` header. This way a
    customer's monitoring stack only ever sees IDs it generated itself.

`X-VL-Request-ID` (internal VulnLedger lineage)
    ALWAYS generated server-side as `VL-<uuid4>`. Always set on the response.
    Incoming `X-VL-Request-ID` headers are always ignored: only VulnLedger's
    own systems get to issue VL-prefixed IDs. Across multi-host deployments,
    VL services should forward `X-VL-Request-ID` to other VL services and
    trust the value; they should never forward `X-Request-ID` for internal
    correlation.

Both IDs are exposed as `contextvars.ContextVar`s so any code in the request
lifecycle (handlers, services, helpers, log filters) can read them without
threading them through function arguments.
"""
from __future__ import annotations

import os
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

VL_REQUEST_ID_PREFIX = "VL-"
BOOT_ID_PREFIX = "BOOT-"

# Per-container-restart boot identifier. The backend container's
# Dockerfile CMD mints this once in the entrypoint shell and exports
# it as the BOOT_ID env var, so the alembic-migration child Python
# process AND the uvicorn child Python process both inherit the same
# value. Without that pattern, each Python process imports this module
# independently and would mint its own UUID, producing two BOOT-<uuid>
# values per restart.
#
# When BOOT_ID is not in the environment (local dev, pytest, ad-hoc
# `docker compose exec backend python -c ...`), mint one here so the
# ContextVar default still has a stable value.
#
# Boot-time code paths (alembic migrations, seed routines, startup
# hooks, or any other non-HTTP execution before the first request)
# inherit this as the default for `vl_request_id_var`, which means
# their structured log lines carry a stable correlation key instead
# of `null`.
#
# HTTP requests overwrite the ContextVar via `.set(VL-<uuid4>)` for
# the per-request task scope. After the request completes, the
# ContextVar falls back to BOOT_ID for any subsequent non-request
# log lines on the same process. Closes #77.
BOOT_ID: str = os.environ.get("BOOT_ID") or f"{BOOT_ID_PREFIX}{uuid.uuid4()}"

# x_request_id stays None by default. It only gets populated when an
# upstream actually sent a valid X-Request-ID header on an incoming
# request; we never invent one. Boot-time logs have no upstream, so
# null is the correct semantic there.
x_request_id_var: ContextVar[Optional[str]] = ContextVar(
    "x_request_id", default=None
)
vl_request_id_var: ContextVar[Optional[str]] = ContextVar(
    "vl_request_id", default=BOOT_ID
)


def _is_valid_uuid(value: str) -> bool:
    """Return True iff value parses as a UUID of any version.

    `uuid.UUID()` raises ValueError on malformed input, including any
    `VL-...` injection attempt (which contains an extra dash group and
    leading non-hex chars).
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _generate_vl_request_id() -> str:
    """Generate a new VulnLedger-prefixed request ID. Format: `VL-<uuid4>`."""
    return f"{VL_REQUEST_ID_PREFIX}{uuid.uuid4()}"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Resolve per-request correlation IDs and stamp response headers.

    Behavior:
      * Read `X-Request-ID` from the incoming request. If it is a valid
        UUID, propagate it; otherwise treat as absent.
      * Always generate a fresh `VL-<uuid4>` for `X-VL-Request-ID`.
      * Always ignore any incoming `X-VL-Request-ID` (security boundary -
        only our systems get to issue VL-prefixed IDs).
      * Set both contextvars before the downstream chain runs so handlers
        and log records pick up the IDs without explicit argument passing.
      * On the way out, set `X-Request-ID` on the response only when
        upstream provided a valid one. Always set `X-VL-Request-ID`.

    Order: register as the OUTERMOST middleware so the contextvars are
    populated before any inner middleware or handler executes.
    """

    async def dispatch(self, request: Request, call_next):
        incoming = (request.headers.get("X-Request-ID") or "").strip()
        x_request_id: Optional[str] = (
            incoming if (incoming and _is_valid_uuid(incoming)) else None
        )
        vl_request_id: str = _generate_vl_request_id()

        # Set the contextvars without a corresponding `reset()`. ContextVars
        # in asyncio are task-local (PEP 567): each request gets its own
        # task with its own context copy, so values do not leak across
        # concurrent requests. Skipping the reset means uvicorn's access
        # log line (which runs AFTER this middleware returns, in the same
        # task) can still see the IDs from the contextvars.
        x_request_id_var.set(x_request_id)
        vl_request_id_var.set(vl_request_id)

        response: Response = await call_next(request)

        if x_request_id is not None:
            response.headers["X-Request-ID"] = x_request_id
        response.headers["X-VL-Request-ID"] = vl_request_id
        return response
