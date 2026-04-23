from datetime import datetime, timezone

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    detail: str
    timestamp: datetime


def make_error_payload(code: str, detail: str) -> dict:
    return ErrorResponse(
        code=code,
        detail=detail,
        timestamp=datetime.now(timezone.utc),
    ).model_dump(mode="json")
