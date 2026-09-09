import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.proposal import ProposalCreate, ProposalOut
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


@router.get("/proposals/mine", response_model=PaginatedResponse[ProposalOut])
def list_my_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = proposal_service.list_my_proposals(db, current_user, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/jobs/{job_id}/proposals", response_model=PaginatedResponse[ProposalOut])
def list_job_proposals(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = proposal_service.list_job_proposals(db, current_user, job_id, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/proposals/{proposal_id}", response_model=ProposalOut)
def get_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return proposal_service.get_proposal(db, current_user, proposal_id)


@router.post("/proposals/{proposal_id}/accept", response_model=ProposalOut)
def accept_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return proposal_service.accept_proposal(db, current_user, proposal_id)


@router.post("/proposals/{proposal_id}/reject", response_model=ProposalOut)
def reject_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return proposal_service.reject_proposal(db, current_user, proposal_id)
