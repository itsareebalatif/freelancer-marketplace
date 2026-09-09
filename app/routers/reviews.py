import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewCreate, ReviewOut
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.post(
    "/contracts/{contract_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def create_review(
    contract_id: uuid.UUID,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_service.create_review(db, current_user, contract_id, data)


@router.get("/contracts/{contract_id}/reviews", response_model=list[ReviewOut])
def list_contract_reviews(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_service.list_contract_reviews(db, current_user, contract_id)


@router.get("/users/{user_id}/reviews", response_model=PaginatedResponse[ReviewOut])
def list_user_reviews(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = review_service.list_user_reviews(db, user_id, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
