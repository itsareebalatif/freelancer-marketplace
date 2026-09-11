import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.contract import Contract
from app.models.enums import ContractStatus, MilestoneStatus
from app.models.user import User
from app.repositories.contract_repo import ContractRepository
from app.repositories.milestone_repo import MilestoneRepository

logger = logging.getLogger(__name__)


def list_my_contracts(db: Session, user: User, *, page: int, page_size: int):
    return ContractRepository(db).list_for_user(user.id, page=page, page_size=page_size)


def get_contract(db: Session, user: User, contract_id) -> Contract:
    contract = ContractRepository(db).get_by_id(contract_id)
    if contract is None:
        raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")

    if user.id not in (contract.client_id, contract.freelancer_id):
        raise ForbiddenError("You are not a participant of this contract", code="CONTRACT_ACCESS_DENIED")

    return contract


def _complete_contract(db: Session, user: User, contract: Contract) -> Contract:
    if contract.client_id != user.id:
        raise ForbiddenError("Only the client can complete this contract", code="NOT_CONTRACT_CLIENT")

    if contract.status != ContractStatus.ACTIVE:
        raise ConflictError("Contract is not active", code="CONTRACT_NOT_ACTIVE")

    milestones = MilestoneRepository(db).list_by_contract(contract.id)
    if not milestones:
        raise ConflictError("Contract has no milestones to complete", code="NO_MILESTONES")

    if any(m.status != MilestoneStatus.APPROVED for m in milestones):
        raise ConflictError(
            "All milestones must be approved before the contract can be completed",
            code="MILESTONES_INCOMPLETE",
        )

    contract = ContractRepository(db).update(
        contract, status=ContractStatus.COMPLETED, completed_at=datetime.now(timezone.utc)
    )
    logger.info("Contract %s completed by client %s", contract.id, user.id)
    return contract


def update_contract(db: Session, user: User, contract_id, data) -> Contract:
    contract = ContractRepository(db).get_by_id(contract_id)
    if contract is None:
        raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")

    new_status = data.model_dump(exclude_unset=True).get("status")
    if new_status is None:
        raise ConflictError("Nothing to update — pass a status", code="NO_CHANGES")

    if new_status != ContractStatus.COMPLETED:
        raise ConflictError(
            "Status can only be set to COMPLETED via this endpoint", code="STATUS_NOT_CLIENT_SETTABLE"
        )

    return _complete_contract(db, user, contract)
