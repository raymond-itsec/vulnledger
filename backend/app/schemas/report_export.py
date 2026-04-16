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
    created_by: UUID
    created_by_name: str | None = None
    exported_at: datetime

    model_config = {"from_attributes": True}
