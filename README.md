freelancer-marketplace/
├── .env.example                  # Template for all secrets & config (DB URL, JWT secrets, port)
├── .gitignore                    # Ignore venv, .env, __pycache__, .pytest_cache
├── pyproject.toml                # Managed via `uv` dependency manager
├── uv.lock                       # Deterministic lockfile
├── Dockerfile                    # Containerization for Railway deployment
├── railway.json                  # Railway build & deploy configuration (runs migrations & app)
├── alembic.ini                   # Alembic migration configuration
├── README.md                     # Setup, workflow explanations, and API guide
│
├── alembic/                      # Database migration scripts
│   ├── env.py                    # Imports Base & models for autogenerate
│   ├── script.py.mako
│   └── versions/                 # Version migration files
│
├── tests/                        # Automated Pytest suite
│   ├── conftest.py               # Test DB session fixtures, mock clients, auth headers
│   ├── test_auth.py              # Registration, login, refresh token rotation, logout
│   ├── test_jobs.py              # Job posting, search, filtering, and role checks
│   ├── test_proposals.py         # Submitting proposals, duplicate prevention
│   ├── test_contracts.py         # Proposal acceptance transaction & contract creation
│   ├── test_milestones.py        # Milestone transitions and approval flows
│   └── test_reviews.py           # Review eligibility and duplicate review checks
│
└── app/
    ├── __init__.py
    ├── main.py                   # FastAPI initialization, CORS, routers inclusion, health check
    │
    ├── core/                     # Application configurations & security primitives
    │   ├── __init__.py
    │   ├── config.py             # Pydantic BaseSettings (DB_URL, JWT secret, token lifespans)
    │   ├── security.py           # Password hashing (bcrypt) & JWT encoding/decoding
    │   └── exceptions.py         # Custom domain exceptions & global exception handlers
    │
    ├── db/                       # Database engine setup and session management
    │   ├── __init__.py
    │   ├── session.py            # SQLAlchemy engine, sessionmaker, and get_db dependency
    │   └── base.py               # Base class importing all models (for Alembic metadata)
    │
    ├── models/                   # SQLAlchemy ORM database models
    │   ├── __init__.py
    │   ├── user.py               # User table (roles: CLIENT, FREELANCER) & RefreshToken table
    │   ├── profile.py            # FreelancerProfile and Skill association tables
    │   ├── job.py                # Job and JobSkill association tables
    │   ├── proposal.py           # Proposal table (cover letter, bid amount, status)
    │   ├── contract.py           # Contract table (client_id, freelancer_id, status)
    │   ├── milestone.py          # Milestone table (amount, deadline, status)
    │   └── review.py             # Review table (rating, comment, reviewer/reviewee IDs)
    │
    ├── schemas/                  # Pydantic schemas (Request, Response, Validation)
    │   ├── __init__.py
    │   ├── common.py             # Reusable pagination, sorting, and base response schemas
    │   ├── auth.py               # Token schemas, LoginRequest, RegisterRequest
    │   ├── user.py               # UserRead, UserUpdate
    │   ├── profile.py            # ProfileCreate, ProfileUpdate, ProfileRead, SkillSchema
    │   ├── job.py                # JobCreate, JobUpdate, JobRead, JobFilterParams
    │   ├── proposal.py           # ProposalCreate, ProposalUpdate, ProposalRead
    │   ├── contract.py           # ContractRead, ContractStatusUpdate
    │   ├── milestone.py          # MilestoneCreate, MilestoneStatusUpdate, MilestoneRead
    │   └── review.py             # ReviewCreate, ReviewRead
    │
    ├── repositories/             # Direct database queries & CRUD (SQLAlchemy abstraction)
    │   ├── __init__.py
    │   ├── base.py               # Generic CRUD repository helper (optional)
    │   ├── user_repo.py          # Query users, credentials, and refresh tokens
    │   ├── profile_repo.py       # Query and update freelancer profiles & skills
    │   ├── job_repo.py           # Query, filter, and paginate job postings
    │   ├── proposal_repo.py      # Query, count, and fetch proposals per job
    │   ├── contract_repo.py      # Query contracts and participant relationships
    │   ├── milestone_repo.py     # Query and update milestones
    │   └── review_repo.py        # Query reviews and duplicate constraints
    │
    ├── services/                 # Business logic, state transitions, & transactions
    │   ├── __init__.py
    │   ├── auth_service.py       # Authentication, token rotation, and logout revocation
    │   ├── job_service.py        # Job publishing rules and ownership checks
    │   ├── proposal_service.py   # Proposal eligibility and validation rules
    │   ├── contract_service.py   # Atomic transaction: accept proposal + build contract
    │   ├── milestone_service.py  # Milestone status transitions and contract completion checks
    │   └── review_service.py     # Post-contract review eligibility validation
    │
    ├── dependencies/             # FastAPI Depends() providers
    │   ├── __init__.py
    │   ├── auth.py               # get_current_user, token decoder
    │   └── permissions.py        # require_client, require_freelancer, check_ownership
    │
    └── routers/                  # API endpoints (HTTP routing, status codes, documentation)
        ├── __init__.py
        ├── auth.py               # /auth/register, /auth/login, /auth/refresh, /auth/logout
        ├── users.py              # /users/me
        ├── profiles.py           # /profiles (freelancer bio, hourly rate, skills)
        ├── skills.py             # /skills (browse, list, search available skills)
        ├── jobs.py               # /jobs (create, search, filter, paginate, update, close)
        ├── proposals.py          # /jobs/{id}/proposals, /proposals/{id}/accept
        ├── contracts.py          # /contracts/{id}, /contracts/{id}/complete
        ├── milestones.py         # /contracts/{id}/milestones, /milestones/{id}/submit
        └── reviews.py            # /contracts/{id}/reviews