import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Text, Numeric, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BudgetType, ExperienceLevel, JobDuration, JobStatus, LocationType

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
    budget_type: Mapped[BudgetType] = mapped_column(
        Enum(BudgetType, native_enum=False), default=BudgetType.FIXED, nullable=False
    )
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, native_enum=False), default=ExperienceLevel.INTERMEDIATE, nullable=False
    )
    duration: Mapped[Optional[JobDuration]] = mapped_column(
        Enum(JobDuration, native_enum=False), nullable=True
    )
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, native_enum=False), default=LocationType.REMOTE, index=True, nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped["User"] = relationship(back_populates="jobs")
    skills: Mapped[List["Skill"]] = relationship(secondary="job_skills", back_populates="jobs")
    proposals: Mapped[List["Proposal"]] = relationship(back_populates="job", cascade="all, delete-orphan")