import enum

class UserRole(str, enum.Enum):
    CLIENT="CLIENT"
    FREELANCER="FREELANCER"

class JobStatus(str, enum.Enum):
    DRAFT="DRAFT"
    PUBLISHED="PUBLISHED"
    IN_PROGRESS="IN_PROGRESS"
    COMPLETED="COMPLETED"
    CLOSED="CLOSED"

class ProposalStatus(str, enum.Enum):
    PENDING="PENDING"
    ACCEPTED="ACCEPTED"
    REJECTED="REJECTED"

class ContractStatus(str, enum.Enum):
    ACTIVE="ACTIVE"
    COMPLETED="COMPLETED"
    TERMINATED="TERMINATED"

class MilestoneStatus(str, enum.Enum):
    PENDING="PENDING"
    SUBMITTED="SUBMITTED"
    APPROVED="APPROVED"
    REJECTED="REJECTED"

class BudgetType(str, enum.Enum):
    FIXED="FIXED"
    HOURLY="HOURLY"

class ExperienceLevel(str, enum.Enum):
    ENTRY="ENTRY"
    INTERMEDIATE="INTERMEDIATE"
    EXPERT="EXPERT"

class JobDuration(str, enum.Enum):
    LESS_THAN_1_MONTH="LESS_THAN_1_MONTH"
    ONE_TO_3_MONTHS="ONE_TO_3_MONTHS"
    THREE_TO_6_MONTHS="THREE_TO_6_MONTHS"
    MORE_THAN_6_MONTHS="MORE_THAN_6_MONTHS"

class LocationType(str, enum.Enum):
    REMOTE="REMOTE"
    ONSITE="ONSITE"
    HYBRID="HYBRID"
