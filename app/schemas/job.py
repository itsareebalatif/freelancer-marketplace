import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobStatus
from app.schemas.profile import SkillOut


class JobCreate(BaseModel):
    title: str
    description: str
    budget: Decimal


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[Decimal] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    title: str
    description: str
    budget: Decimal
    status: JobStatus
    skills: list[SkillOut]
    created_at: datetime
