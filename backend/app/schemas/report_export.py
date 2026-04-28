from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportExportResponse(BaseModel):
    export_id: UUID
    session_id: UUID
    file_name: str
    report_format: str
    content_type: str
    size_bytes: int
    sha256: str | None = None
    locked_until: datetime | None = None
    retention_expires_at: datetime | None = None
    created_by: UUID
    created_by_name: str | None = None
    exported_at: datetime

    model_config = {"from_attributes": True}
