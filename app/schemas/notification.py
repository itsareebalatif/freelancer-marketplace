import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationChannel, NotificationEventType, NotificationStatus


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: NotificationEventType
    channel: NotificationChannel
    status: NotificationStatus
    subject: Optional[str]
    attempt_count: int
    last_error: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime


class NotificationPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: NotificationEventType
    email_enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    event_type: NotificationEventType
    email_enabled: bool


class NotificationPreferencesUpdateRequest(BaseModel):
    preferences: list[NotificationPreferenceUpdate]
