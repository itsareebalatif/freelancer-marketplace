from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserSummaryOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/summary", response_model=UserSummaryOut)
def get_my_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.get_summary(db, current_user)
