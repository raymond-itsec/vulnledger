import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class TaxonomyVersion(Base, TimestampMixin):
    __tablename__ = "taxonomy_versions"

    taxonomy_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    entries = relationship(
        "TaxonomyEntry",
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="TaxonomyEntry.domain, TaxonomyEntry.sort_order, TaxonomyEntry.value",
    )


class TaxonomyEntry(Base):
    __tablename__ = "taxonomy_entries"
    __table_args__ = (
        UniqueConstraint(
            "taxonomy_version_id", "domain", "value", name="uq_taxonomy_entry_value"
        ),
    )

    taxonomy_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    taxonomy_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("taxonomy_versions.taxonomy_version_id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    version = relationship("TaxonomyVersion", back_populates="entries")
