import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.milestone import MilestoneOut, MilestoneUpdate
from app.services import milestone_service

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("/{milestone_id}", response_model=MilestoneOut)
def get_milestone(
    milestone_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return milestone_service.get_milestone(db, current_user, milestone_id)


@router.patch("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: uuid.UUID,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return milestone_service.update_milestone(db, current_user, milestone_id, data)
