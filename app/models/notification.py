import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import NotificationChannel, NotificationEventType, NotificationStatus


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, native_enum=False), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False), default=NotificationStatus.PENDING, nullable=False
    )
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, native_enum=False), nullable=False
    )
    email_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "event_type", name="uq_user_event_preference"),
    )

    user: Mapped["User"] = relationship()
