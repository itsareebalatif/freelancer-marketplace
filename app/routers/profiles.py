import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.profile import FreelancerProfileCreate, FreelancerProfileOut, FreelancerProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])

require_freelancer = require_role(UserRole.FREELANCER)


@router.post("", response_model=FreelancerProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: FreelancerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return profile_service.create_profile(db, current_user, data)


@router.get("", response_model=FreelancerProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return profile_service.get_my_profile(db, current_user)


@router.patch("", response_model=FreelancerProfileOut)
def update_profile(
    data: FreelancerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return profile_service.update_profile(db, current_user, data)


@router.post("/skills/{skill_id}", response_model=FreelancerProfileOut)
def add_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return profile_service.add_skill(db, current_user, skill_id)


@router.delete("/skills/{skill_id}", response_model=FreelancerProfileOut)
def remove_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer),
):
    return profile_service.remove_skill(db, current_user, skill_id)
