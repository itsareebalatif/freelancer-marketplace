import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class SkillCreate(BaseModel):
    name: str


class FreelancerProfileCreate(BaseModel):
    bio: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    experience_years: int = 0
    availability: str = "Available"


class FreelancerProfileUpdate(BaseModel):
    bio: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    experience_years: Optional[int] = None
    availability: Optional[str] = None


class FreelancerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    bio: Optional[str]
    hourly_rate: Optional[Decimal]
    experience_years: int
    availability: str
    skills: list[SkillOut]
    created_at: datetime
