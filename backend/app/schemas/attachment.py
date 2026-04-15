from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    attachment_id: UUID
    finding_id: UUID
    file_name: str
    content_type: str | None
    size_bytes: int | None
    uploaded_by: UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}
