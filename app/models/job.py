import uuid
from decimal import Decimal
from typing import List
from sqlalchemy import String, Text, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import JobStatus

class JobSkill(Base):
    """Junction table mapping Many-to-Many: Jobs <-> Skills"""
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False), 
        default=JobStatus.DRAFT, 
        index=True, 
        nullable=False
    )

    # Relationships
    client: Mapped["User"] = relationship(back_populates="jobs")
    skills: Mapped[List["Skill"]] = relationship(secondary="job_skills", back_populates="jobs")
    proposals: Mapped[List["Proposal"]] = relationship(back_populates="job", cascade="all, delete-orphan")