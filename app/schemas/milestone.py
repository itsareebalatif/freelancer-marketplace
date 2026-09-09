import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MilestoneStatus


class MilestoneCreate(BaseModel):
    title: str
    amount: Decimal = Field(gt=0)
    deadline: Optional[datetime] = None


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    title: str
    amount: Decimal
    deadline: Optional[datetime]
    status: MilestoneStatus
    created_at: datetime
