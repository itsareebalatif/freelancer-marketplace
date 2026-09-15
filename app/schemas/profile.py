import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FreelancerProfileCreate(BaseModel):
    bio: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    experience_years: int = 0
    availability: str = "Available"
    skills: list[str] = []


class FreelancerProfileUpdate(BaseModel):
    bio: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    experience_years: Optional[int] = None
    availability: Optional[str] = None
    skills: Optional[list[str]] = None


class FreelancerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    bio: Optional[str]
    hourly_rate: Optional[Decimal]
    experience_years: int
    availability: str
    avatar_attachment_id: Optional[uuid.UUID]
    skills: list[str]
    created_at: datetime
