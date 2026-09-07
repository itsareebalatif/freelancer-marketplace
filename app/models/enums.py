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
