import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.Session import get_db
from app.dependencies import get_current_user_optional, require_role
from app.models.enums import JobStatus, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.job import JobCreate, JobOut, JobSearchFilters, JobUpdate
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


@router.post("/search", response_model=PaginatedResponse[JobOut])
def search_jobs(
    filters: JobSearchFilters = JobSearchFilters(),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    search: Optional[str] = None,
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
):
    if filters.mine:
        if current_user is None:
            raise UnauthorizedError("Authentication required", code="NOT_AUTHENTICATED")
        if current_user.role != UserRole.CLIENT:
            raise ForbiddenError("This action requires the client role", code="ROLE_NOT_ALLOWED")
        items, total = job_service.list_my_jobs(
            db, current_user, page=filters.page, page_size=filters.page_size, status=status_filter
        )
        return PaginatedResponse(items=items, total=total, page=filters.page, page_size=filters.page_size)

    # Public browse always stays locked to PUBLISHED jobs — a `status` filter here
    # is ignored rather than honored, since exposing other clients' DRAFT/CLOSED
    # jobs to anonymous visitors would be a data leak, not a feature.
    items, total = job_service.list_jobs(
        db,
        page=filters.page,
        page_size=filters.page_size,
        search=search,
        skill_id=filters.skill_id,
        category=filters.category,
        budget_type=filters.budget_type,
        experience_level=filters.experience_level,
        location_type=filters.location_type,
        sort_by=filters.sort_by,
    )
    return PaginatedResponse(items=items, total=total, page=filters.page, page_size=filters.page_size)


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
