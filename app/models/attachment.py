import uuid
from sqlalchemy import String, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AttachmentResourceType


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    resource_type: Mapped[AttachmentResourceType] = mapped_column(
        Enum(AttachmentResourceType, native_enum=False), index=True, nullable=False
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("resource_type", "resource_id", "checksum", name="uq_resource_checksum"),
    )

    owner: Mapped["User"] = relationship()
