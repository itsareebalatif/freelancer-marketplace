from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.db.Session import get_db
from app.dependencies import get_current_user
from app.models.enums import NotificationEventType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.notification import (
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferencesUpdateRequest,
)
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = notification_service.list_my_notifications(db, current_user, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/preferences", response_model=list[NotificationPreferenceOut])
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return notification_service.get_preferences(db, current_user)


@router.patch("/preferences", response_model=list[NotificationPreferenceOut])
def update_preferences(
    data: NotificationPreferencesUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updates = [p.model_dump() for p in data.preferences]
    return notification_service.update_preferences(db, current_user, updates)


@router.post("/test", status_code=202)
def send_test_notification(current_user: User = Depends(get_current_user)):
    if settings.ENV == "production":
        raise ForbiddenError("Test notifications are disabled in production", code="TEST_ENDPOINT_DISABLED")

    notification_service.send_test_email(current_user)
    return {"detail": "Test email sent"}
