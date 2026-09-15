import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime


class UserSummaryOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    role: UserRole
    created_at: datetime

    # Freelancer profile snapshot — None for clients, or for a freelancer who
    # hasn't created a profile yet.
    bio: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    avatar_attachment_id: Optional[uuid.UUID] = None
    skills: Optional[list[str]] = None

    # Client-only stats.
    jobs_by_status: Optional[dict[str, int]] = None
    proposals_received: Optional[int] = None

    # Freelancer-only stats.
    proposals_by_status: Optional[dict[str, int]] = None

    # Shared by both roles.
    contracts_by_status: dict[str, int]
    average_rating: Optional[float] = None
