from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.contract_repo import ContractRepository
from app.repositories.job_repo import JobRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.proposal_repo import ProposalRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.user import UserSummaryOut


def get_summary(db: Session, user: User) -> UserSummaryOut:
    contracts_by_status = ContractRepository(db).count_by_status_for_user(user.id)
    average_rating = ReviewRepository(db).average_rating_for_user(user.id)

    fields = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at,
        "contracts_by_status": contracts_by_status,
        "average_rating": average_rating,
    }

    if user.role == UserRole.CLIENT:
        fields["jobs_by_status"] = JobRepository(db).count_by_status_for_client(user.id)
        fields["proposals_received"] = ProposalRepository(db).count_received_for_client(user.id)
    else:
        fields["proposals_by_status"] = ProposalRepository(db).count_by_status_for_freelancer(user.id)

        profile = ProfileRepository(db).get_by_user_id(user.id)
        if profile is not None:
            fields["bio"] = profile.bio
            fields["hourly_rate"] = profile.hourly_rate
            fields["avatar_attachment_id"] = profile.avatar_attachment_id
            fields["skills"] = profile.skills

    return UserSummaryOut(**fields)
