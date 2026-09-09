import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import ContractStatus
from app.schemas.milestone import MilestoneOut


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proposal_id: uuid.UUID
    client_id: uuid.UUID
    freelancer_id: uuid.UUID
    total_amount: Decimal
    status: ContractStatus
    completed_at: Optional[datetime]
    milestones: list[MilestoneOut]
    created_at: datetime
