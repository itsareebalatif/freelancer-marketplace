import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import ContractStatus
from app.models.review import Review
from app.models.user import User
from app.repositories.contract_repo import ContractRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewCreate

logger = logging.getLogger(__name__)


def create_review(db: Session, user: User, contract_id, data: ReviewCreate) -> Review:
    contract = ContractRepository(db).get_by_id(contract_id)
    if contract is None:
        raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")

    if user.id not in (contract.client_id, contract.freelancer_id):
        raise ForbiddenError("You are not a participant of this contract", code="CONTRACT_ACCESS_DENIED")

    if contract.status != ContractStatus.COMPLETED:
        raise ConflictError(
            "A contract must be completed before it can be reviewed", code="CONTRACT_NOT_COMPLETED"
        )

    reviewee_id = contract.freelancer_id if user.id == contract.client_id else contract.client_id

    reviews = ReviewRepository(db)
    if reviews.get_by_contract_and_reviewer(contract_id, user.id) is not None:
        raise ConflictError("You already reviewed this contract", code="DUPLICATE_REVIEW")

    review = reviews.create(
        contract_id=contract_id, reviewer_id=user.id, reviewee_id=reviewee_id, **data.model_dump()
    )
    logger.info("Review %s left on contract %s by %s for %s", review.id, contract_id, user.id, reviewee_id)
    return review


def list_contract_reviews(db: Session, user: User, contract_id) -> list[Review]:
    contract = ContractRepository(db).get_by_id(contract_id)
    if contract is None:
        raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")

    if user.id not in (contract.client_id, contract.freelancer_id):
        raise ForbiddenError("You are not a participant of this contract", code="CONTRACT_ACCESS_DENIED")

    return ReviewRepository(db).list_by_contract(contract_id)


def list_user_reviews(db: Session, user_id, *, page: int, page_size: int):
    return ReviewRepository(db).list_by_reviewee(user_id, page=page, page_size=page_size)
