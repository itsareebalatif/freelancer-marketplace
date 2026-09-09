import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    skill_id: Optional[uuid.UUID] = None,
    sort_by: str = Query("newest", pattern="^(newest|budget_asc|budget_desc)$"),
):
    items, total = job_service.list_jobs(
        db, page=page, page_size=page_size, search=search, skill_id=skill_id, sort_by=sort_by
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/mine", response_model=PaginatedResponse[JobOut])
def list_my_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = job_service.list_my_jobs(db, current_user, page=page, page_size=page_size)
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


@router.post("/{job_id}/publish", response_model=JobOut)
def publish_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.publish_job(db, current_user, job_id)


@router.post("/{job_id}/close", response_model=JobOut)
def close_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.close_job(db, current_user, job_id)


@router.post("/{job_id}/skills/{skill_id}", response_model=JobOut)
def add_job_skill(
    job_id: uuid.UUID,
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.add_skill(db, current_user, job_id, skill_id)


@router.delete("/{job_id}/skills/{skill_id}", response_model=JobOut)
def remove_job_skill(
    job_id: uuid.UUID,
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return job_service.remove_skill(db, current_user, job_id, skill_id)
