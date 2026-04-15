import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("review_sessions.session_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    impact: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    remediation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open"
    )
    references: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    session = relationship("ReviewSession", back_populates="findings")
    history = relationship(
        "FindingHistory", back_populates="finding", lazy="selectin",
        order_by="FindingHistory.changed_at",
    )
    attachments = relationship("FindingAttachment", back_populates="finding", cascade="all, delete-orphan")
