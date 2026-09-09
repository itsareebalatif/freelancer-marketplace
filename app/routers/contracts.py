import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.contract import ContractOut
from app.schemas.milestone import MilestoneCreate, MilestoneOut
from app.services import contract_service, milestone_service

router = APIRouter(prefix="/contracts", tags=["contracts"])

require_client = require_role(UserRole.CLIENT)


@router.get("/mine", response_model=PaginatedResponse[ContractOut])
def list_my_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = contract_service.list_my_contracts(db, current_user, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return contract_service.get_contract(db, current_user, contract_id)


@router.post("/{contract_id}/complete", response_model=ContractOut)
def complete_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return contract_service.complete_contract(db, current_user, contract_id)


@router.post("/{contract_id}/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(
    contract_id: uuid.UUID,
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client),
):
    return milestone_service.create_milestone(db, current_user, contract_id, data)
