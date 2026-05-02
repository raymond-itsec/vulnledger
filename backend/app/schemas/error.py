"""Standard error response shape for every API error.

Canonical envelope (returned by all global exception handlers and any
handler that uses `make_error_payload`):

    {
      "error": {
        "code": "validation_error",
        "message": "Request validation failed.",
        "request_id": "VL-fb16d4ac-...",
        "x_request_id": "abc-...",       (only when upstream provided one)
        "details": {...},                (only when structured payload exists)
        "timestamp": "2026-05-03T12:34:56+00:00"
      }
    }

Field contract:
- `code`         Stable string in snake_case. Frontend can switch on it.
- `message`      Human-readable. May change wording across versions; not a
                 contract. Display, do not parse.
- `request_id`   The `vl_request_id` from the request lifecycle. Always
                 present so a user can paste it in a bug report.
- `x_request_id` The upstream-provided UUID, if any. Field is omitted
                 entirely when no valid X-Request-ID was received.
- `details`      Optional structured payload (per-field validation errors,
                 etc.). Field is omitted entirely when not provided.
- `timestamp`    Server clock at error time, ISO-8601 with `+00:00` UTC
                 marker.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.middleware.request_id import vl_request_id_var, x_request_id_var


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    x_request_id: Optional[str] = None
    details: Optional[Any] = None
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: ErrorBody = Field(...)


def make_error_payload(
    code: str,
    detail: str,
    *,
    details: Optional[Any] = None,
) -> dict:
    """Build the canonical error envelope.

    Pulls the request IDs from the contextvars set by RequestIDMiddleware.
    Outside an HTTP request lifecycle (e.g., startup hooks calling this
    directly) both IDs are None and `x_request_id` is omitted from the
    output. `request_id` will be None too in that case but is still
    included for shape consistency.
    """
    body = ErrorBody(
        code=code,
        message=detail,
        request_id=vl_request_id_var.get(),
        x_request_id=x_request_id_var.get(),
        details=details,
        timestamp=datetime.now(timezone.utc),
    )
    # `exclude_none=True` drops both `x_request_id` and `details` when not
    # populated, while `request_id` stays as null on out-of-request
    # records (callers can distinguish "no upstream ID" from "no request"
    # by checking which field is absent vs null).
    payload = body.model_dump(mode="json", exclude_none=True)
    # Force `request_id` back into the output even when None, because
    # consumers always expect to find this key.
    if "request_id" not in payload:
        payload["request_id"] = None
    return {"error": payload}
