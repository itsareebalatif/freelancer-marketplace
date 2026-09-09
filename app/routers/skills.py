from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user
from app.schemas.profile import SkillCreate, SkillOut
from app.services import skill_service

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return skill_service.list_skills(db)


@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(
    data: SkillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return skill_service.create_skill(db, data)
