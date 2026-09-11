import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.db.Session import get_db
from app.dependencies import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.proposal import ProposalCreate, ProposalOut, ProposalUpdate
from app.services import proposal_service

router = APIRouter(tags=["proposals"])

require_client = require_role(UserRole.CLIENT)
require_freelancer = require_role(UserRole.FREELANCER)


@router.post("/jobs/{job_id}/proposals", response_model=ProposalOut, status_code=status.HTTP_201_CREATED)
def submit_proposal(
    job_id: uuid.UUID,
    data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return proposal_service.submit_proposal(db, current_user, job_id, data)


@router.get("/proposals", response_model=PaginatedResponse[ProposalOut])
def list_proposals(
    job_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if job_id is not None:
        if current_user.role != UserRole.CLIENT:
            raise ForbiddenError("This action requires the client role", code="ROLE_NOT_ALLOWED")
        items, total = proposal_service.list_job_proposals(db, current_user, job_id, page=page, page_size=page_size)
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

    if current_user.role != UserRole.FREELANCER:
        raise ForbiddenError("This action requires the freelancer role", code="ROLE_NOT_ALLOWED")
    items, total = proposal_service.list_my_proposals(db, current_user, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/proposals/{proposal_id}", response_model=ProposalOut)
def get_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return proposal_service.get_proposal(db, current_user, proposal_id)


@router.patch("/proposals/{proposal_id}", response_model=ProposalOut)
def update_proposal(
    proposal_id: uuid.UUID,
    data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return proposal_service.update_proposal(db, current_user, proposal_id, data)
