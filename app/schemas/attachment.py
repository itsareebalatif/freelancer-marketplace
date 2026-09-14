import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttachmentResourceType


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    resource_type: AttachmentResourceType
    resource_id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class AttachmentDownloadOut(BaseModel):
    url: str
    expires_in: int
