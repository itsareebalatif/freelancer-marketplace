import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.milestone import MilestoneOut
from app.services import milestone_service

router = APIRouter(prefix="/milestones", tags=["milestones"])

require_client = require_role(UserRole.CLIENT)
require_freelancer = require_role(UserRole.FREELANCER)


@router.get("/{milestone_id}", response_model=MilestoneOut)
def get_milestone(
    milestone_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return milestone_service.get_milestone(db, current_user, milestone_id)


@router.post("/{milestone_id}/submit", response_model=MilestoneOut)
def submit_milestone(
    milestone_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return milestone_service.submit_milestone(db, current_user, milestone_id)


@router.post("/{milestone_id}/approve", response_model=MilestoneOut)
def approve_milestone(
    milestone_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return milestone_service.approve_milestone(db, current_user, milestone_id)


@router.post("/{milestone_id}/reject", response_model=MilestoneOut)
def reject_milestone(
    milestone_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return milestone_service.reject_milestone(db, current_user, milestone_id)
