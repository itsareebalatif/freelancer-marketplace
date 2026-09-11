import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import BudgetType, ExperienceLevel, JobDuration, JobStatus, LocationType
from app.schemas.profile import SkillOut


class JobCreate(BaseModel):
    title: str
    description: str
    budget: Decimal
    budget_type: BudgetType = BudgetType.FIXED
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    duration: Optional[JobDuration] = None
    location_type: LocationType = LocationType.REMOTE
    category: Optional[str] = None
    deadline: Optional[datetime] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[Decimal] = None
    budget_type: Optional[BudgetType] = None
    experience_level: Optional[ExperienceLevel] = None
    duration: Optional[JobDuration] = None
    location_type: Optional[LocationType] = None
    category: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[JobStatus] = None
    skill_ids: Optional[list[uuid.UUID]] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    title: str
    description: str
    budget: Decimal
    budget_type: BudgetType
    experience_level: ExperienceLevel
    duration: Optional[JobDuration]
    location_type: LocationType
    category: Optional[str]
    deadline: Optional[datetime]
    status: JobStatus
    skills: list[SkillOut]
    created_at: datetime
