import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.contract import Contract
from app.models.enums import JobStatus, ProposalStatus
from app.models.proposal import Proposal
from app.models.user import User
from app.repositories.job_repo import JobRepository
from app.repositories.proposal_repo import ProposalRepository
from app.schemas.proposal import ProposalCreate

logger = logging.getLogger(__name__)


def submit_proposal(db: Session, freelancer: User, job_id, data: ProposalCreate) -> Proposal:
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found", code="JOB_NOT_FOUND")

    if job.client_id == freelancer.id:
        raise ForbiddenError("You cannot submit a proposal to your own job", code="OWN_JOB_PROPOSAL")

    if job.status != JobStatus.PUBLISHED:
        raise ConflictError("This job is not open for proposals", code="JOB_NOT_OPEN")

    proposals = ProposalRepository(db)
    if proposals.get_by_job_and_freelancer(job_id, freelancer.id) is not None:
        raise ConflictError("You already submitted a proposal for this job", code="DUPLICATE_PROPOSAL")

    proposal = proposals.create(job_id=job_id, freelancer_id=freelancer.id, **data.model_dump())
    logger.info("Proposal %s submitted by freelancer %s for job %s", proposal.id, freelancer.id, job_id)
    return proposal


def list_my_proposals(db: Session, freelancer: User, *, page: int, page_size: int):
    return ProposalRepository(db).list_by_freelancer(freelancer.id, page=page, page_size=page_size)


def list_job_proposals(db: Session, client: User, job_id, *, page: int, page_size: int):
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found", code="JOB_NOT_FOUND")
    if job.client_id != client.id:
        raise ForbiddenError("You don't own this job", code="NOT_JOB_OWNER")

    return ProposalRepository(db).list_by_job(job_id, page=page, page_size=page_size)


def get_proposal(db: Session, user: User, proposal_id) -> Proposal:
    proposal = ProposalRepository(db).get_by_id(proposal_id)
    if proposal is None:
        raise NotFoundError("Proposal not found", code="PROPOSAL_NOT_FOUND")

    job = JobRepository(db).get_by_id(proposal.job_id)
    is_owning_freelancer = proposal.freelancer_id == user.id
    is_owning_client = job is not None and job.client_id == user.id
    if not (is_owning_freelancer or is_owning_client):
        raise ForbiddenError("You can't view this proposal", code="PROPOSAL_ACCESS_DENIED")

    return proposal


def reject_proposal(db: Session, client: User, proposal_id) -> Proposal:
    proposal = ProposalRepository(db).get_by_id(proposal_id)
    if proposal is None:
        raise NotFoundError("Proposal not found", code="PROPOSAL_NOT_FOUND")

    job = JobRepository(db).get_by_id(proposal.job_id)
    if job is None or job.client_id != client.id:
        raise ForbiddenError("You don't own this job", code="NOT_JOB_OWNER")

    if proposal.status != ProposalStatus.PENDING:
        raise ConflictError(
            "Only a pending proposal can be rejected", code="INVALID_PROPOSAL_STATUS_TRANSITION"
        )

    proposal = ProposalRepository(db).update_status(proposal, ProposalStatus.REJECTED)
    logger.info("Proposal %s rejected by client %s", proposal.id, client.id)
    return proposal


def accept_proposal(db: Session, client: User, proposal_id) -> Proposal:
    proposal = ProposalRepository(db).get_by_id(proposal_id)
    if proposal is None:
        raise NotFoundError("Proposal not found", code="PROPOSAL_NOT_FOUND")

    job = JobRepository(db).get_by_id(proposal.job_id)
    if job is None or job.client_id != client.id:
        raise ForbiddenError("You don't own this job", code="NOT_JOB_OWNER")

    if job.status != JobStatus.PUBLISHED:
        raise ConflictError(
            "This job is not open — it may already be in progress or closed", code="JOB_NOT_OPEN"
        )

    if proposal.status != ProposalStatus.PENDING:
        raise ConflictError(
            "Only a pending proposal can be accepted", code="INVALID_PROPOSAL_STATUS_TRANSITION"
        )

    # Everything below happens in ONE database transaction (a single commit at the
    # end). Accepting a proposal touches four different things at once — the
    # proposal itself, every rival proposal on the same job, the job's status, and
    # a brand-new contract. If we committed after each step and the process died
    # halfway through, we could end up with a proposal marked ACCEPTED but no
    # contract behind it, or a job stuck IN_PROGRESS with no accepted proposal.
    # Committing once, only after every change is staged, means either all of it
    # lands or none of it does.
    other_pending = ProposalRepository(db).list_pending_for_job_excluding(job.id, proposal.id)
    for other in other_pending:
        other.status = ProposalStatus.REJECTED

    proposal.status = ProposalStatus.ACCEPTED
    job.status = JobStatus.IN_PROGRESS

    contract = Contract(
        proposal_id=proposal.id,
        client_id=job.client_id,
        freelancer_id=proposal.freelancer_id,
        total_amount=proposal.bid_amount,
    )
    db.add(contract)
    db.commit()
    db.refresh(proposal)

    logger.info(
        "Proposal %s accepted by client %s — contract %s created, %d rival proposal(s) rejected",
        proposal.id,
        client.id,
        contract.id,
        len(other_pending),
    )
    return proposal
