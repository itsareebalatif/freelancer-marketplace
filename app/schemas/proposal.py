import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProposalStatus


class ProposalCreate(BaseModel):
    cover_letter: str
    bid_amount: Decimal
    estimated_duration: str


class ProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    freelancer_id: uuid.UUID
    cover_letter: str
    bid_amount: Decimal
    estimated_duration: str
    status: ProposalStatus
    created_at: datetime
