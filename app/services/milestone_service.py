import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.contract import Milestone
from app.models.enums import ContractStatus, MilestoneStatus
from app.models.user import User
from app.repositories.contract_repo import ContractRepository
from app.repositories.milestone_repo import MilestoneRepository
from app.schemas.milestone import MilestoneCreate

logger = logging.getLogger(__name__)


def _get_contract_for(db: Session, contract_id):
    contract = ContractRepository(db).get_by_id(contract_id)
    if contract is None:
        raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")
    return contract


def create_milestone(db: Session, user: User, contract_id, data: MilestoneCreate) -> Milestone:
    contract = _get_contract_for(db, contract_id)
    if contract.client_id != user.id:
        raise ForbiddenError("Only the client can add milestones to this contract", code="NOT_CONTRACT_CLIENT")

    if contract.status != ContractStatus.ACTIVE:
        raise ConflictError("Contract is not active", code="CONTRACT_NOT_ACTIVE")

    milestone = MilestoneRepository(db).create(contract_id=contract.id, **data.model_dump())
    logger.info("Milestone %s created for contract %s by client %s", milestone.id, contract.id, user.id)
    return milestone


def _get_visible_milestone(db: Session, user: User, milestone_id) -> tuple[Milestone, object]:
    milestone = MilestoneRepository(db).get_by_id(milestone_id)
    if milestone is None:
        raise NotFoundError("Milestone not found", code="MILESTONE_NOT_FOUND")

    contract = _get_contract_for(db, milestone.contract_id)
    if user.id not in (contract.client_id, contract.freelancer_id):
        raise ForbiddenError("You are not a participant of this contract", code="CONTRACT_ACCESS_DENIED")

    return milestone, contract


def get_milestone(db: Session, user: User, milestone_id) -> Milestone:
    milestone, _ = _get_visible_milestone(db, user, milestone_id)
    return milestone


def submit_milestone(db: Session, user: User, milestone_id) -> Milestone:
    milestone, contract = _get_visible_milestone(db, user, milestone_id)
    if contract.freelancer_id != user.id:
        raise ForbiddenError(
            "Only the assigned freelancer can submit this milestone", code="NOT_CONTRACT_FREELANCER"
        )

    if contract.status != ContractStatus.ACTIVE:
        raise ConflictError("Contract is not active", code="CONTRACT_NOT_ACTIVE")

    if milestone.status not in (MilestoneStatus.PENDING, MilestoneStatus.REJECTED):
        raise ConflictError(
            "Only a pending or rejected milestone can be submitted", code="INVALID_MILESTONE_STATUS_TRANSITION"
        )

    milestone = MilestoneRepository(db).update_status(milestone, MilestoneStatus.SUBMITTED)
    logger.info("Milestone %s submitted by freelancer %s", milestone.id, user.id)
    return milestone


def _client_review_milestone(db: Session, user: User, milestone_id, new_status: MilestoneStatus) -> Milestone:
    milestone, contract = _get_visible_milestone(db, user, milestone_id)
    if contract.client_id != user.id:
        raise ForbiddenError("Only the client can review this milestone", code="NOT_CONTRACT_CLIENT")

    if contract.status != ContractStatus.ACTIVE:
        raise ConflictError("Contract is not active", code="CONTRACT_NOT_ACTIVE")

    if milestone.status != MilestoneStatus.SUBMITTED:
        raise ConflictError(
            "Only a submitted milestone can be reviewed", code="INVALID_MILESTONE_STATUS_TRANSITION"
        )

    milestone = MilestoneRepository(db).update_status(milestone, new_status)
    logger.info("Milestone %s %s by client %s", milestone.id, new_status.value.lower(), user.id)
    return milestone


def approve_milestone(db: Session, user: User, milestone_id) -> Milestone:
    return _client_review_milestone(db, user, milestone_id, MilestoneStatus.APPROVED)


def reject_milestone(db: Session, user: User, milestone_id) -> Milestone:
    return _client_review_milestone(db, user, milestone_id, MilestoneStatus.REJECTED)
