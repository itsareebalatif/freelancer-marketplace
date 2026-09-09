import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Numeric, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ProposalStatus

class Proposal(Base, TimestampMixin):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    freelancer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    bid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_duration: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus, native_enum=False), 
        default=ProposalStatus.PENDING, 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("job_id", "freelancer_id", name="uq_job_freelancer_proposal"),
    )

    job: Mapped["Job"] = relationship(back_populates="proposals")
    freelancer: Mapped["User"] = relationship(back_populates="proposals")
    contract: Mapped[Optional["Contract"]] = relationship(back_populates="proposal", uselist=False)