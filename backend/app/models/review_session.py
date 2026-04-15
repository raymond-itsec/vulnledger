import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class ReviewSession(Base, TimestampMixin):
    __tablename__ = "review_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewed_assets.asset_id"), nullable=False
    )
    review_name: Mapped[str] = mapped_column(String(255), nullable=False)
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned")
    notes: Mapped[str | None] = mapped_column(Text)

    asset = relationship("ReviewedAsset", back_populates="sessions")
    reviewer = relationship("User")
    findings = relationship("Finding", back_populates="session", lazy="selectin")
