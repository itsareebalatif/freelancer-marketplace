import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.Session import get_db
from app.dependencies import get_current_user_optional, require_role
from app.models.enums import BudgetType, ExperienceLevel, JobStatus, LocationType, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.job import JobCreate, JobOut, JobUpdate
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])

require_client = require_role(UserRole.CLIENT)


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.create_job(db, current_user, data)


@router.get("", response_model=PaginatedResponse[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    mine: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    skill_id: Optional[uuid.UUID] = None,
    category: Optional[str] = None,
    budget_type: Optional[BudgetType] = None,
    experience_level: Optional[ExperienceLevel] = None,
    location_type: Optional[LocationType] = None,
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    sort_by: str = Query("newest", pattern="^(newest|budget_asc|budget_desc)$"),
):
    if mine:
        if current_user is None:
            raise UnauthorizedError("Authentication required", code="NOT_AUTHENTICATED")
        if current_user.role != UserRole.CLIENT:
            raise ForbiddenError("This action requires the client role", code="ROLE_NOT_ALLOWED")
        items, total = job_service.list_my_jobs(
            db, current_user, page=page, page_size=page_size, status=status_filter
        )
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

    # Public browse always stays locked to PUBLISHED jobs — a `status` filter here
    # is ignored rather than honored, since exposing other clients' DRAFT/CLOSED
    # jobs to anonymous visitors would be a data leak, not a feature.
    items, total = job_service.list_jobs(
        db,
        page=page,
        page_size=page_size,
        search=search,
        skill_id=skill_id,
        category=category,
        budget_type=budget_type,
        experience_level=experience_level,
        location_type=location_type,
        sort_by=sort_by,
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    return job_service.get_job(db, job_id)


@router.patch("/{job_id}", response_model=JobOut)
def update_job(
    job_id: uuid.UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.update_job(db, current_user, job_id, data)
