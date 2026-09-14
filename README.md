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
│   ├── test_reviews.py           # Review eligibility and duplicate review checks
│   └── test_notifications.py     # Notification delivery, retries, idempotency, preferences
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
        ├── reviews.py            # /contracts/{id}/reviews
        └── notifications.py      # /api/notifications, /api/notifications/preferences, /api/notifications/test


## Email notifications

Event-driven email notifications, sent through [Resend](https://resend.com).

**Design decision:** Supabase's built-in email delivery only covers Supabase Auth flows (signup/reset
emails). This project uses its own JWT auth, not Supabase Auth, so there's nothing to hook into there.
Instead, the notification module calls the Resend API directly from the FastAPI backend — the API key
never leaves the server — and stores all event/delivery state in the same Supabase-hosted Postgres
database the rest of the app already uses.

**Environment variables** (see `.env.example`):
- `RESEND_API_KEY` — Resend API key.
- `EMAIL_FROM_ADDRESS` — verified sender address (defaults to `onboarding@resend.dev`, Resend's shared
  sandbox sender, which can only deliver to the email address on the Resend account until a custom
  domain is verified).
- `ENV` — set to `production` to disable `POST /api/notifications/test`.

**Architecture** (`app/services/notification_service.py`):
- `notify(db, user, event_type, context, resource_id=...)` is called by business services (never by
  routers) after their own transaction has already committed, so a notification problem can never roll
  back a successful proposal/contract/milestone action.
- Each call first checks the `notifications` table for an existing row with the same
  `idempotency_key` (`"{event_type}:{resource_id}"`). If one exists, the call is a no-op — this is what
  makes retried requests safe from duplicate emails.
- It then checks `notification_preferences` for that user/event; if the user opted out, a `SKIPPED` row
  is recorded and nothing is sent.
- Otherwise it renders the event's template (`app/services/notification_templates.py`), calls Resend
  through `app/core/email_provider.py`, and records the result as `SENT` or `FAILED` (with the error
  message) on the same `notifications` row. The whole pipeline is wrapped in a catch-all so a Resend
  outage or bug never bubbles up into the calling request.
- Delivery is synchronous (inline in the request) rather than via a background queue — the Resend call
  is a single fast HTTP request, and this kept the implementation simple. If delivery volume grows, the
  same `notify()` call can be swapped to hand off to `BackgroundTasks` or a real queue without changing
  any call site.

**Events wired up:** `USER_REGISTERED` (registration), `PROPOSAL_RECEIVED` (submit proposal → notifies
the job's client), `PROPOSAL_ACCEPTED` / `PROPOSAL_REJECTED` / `CONTRACT_CREATED` (client decides on a
proposal → notifies the freelancer), `MILESTONE_SUBMITTED` (→ notifies the client),
`MILESTONE_APPROVED` / `MILESTONE_REJECTED` (→ notifies the freelancer), `CONTRACT_COMPLETED` (→
notifies the freelancer), `REVIEW_RECEIVED` (→ notifies the reviewee).

**Known simplification:** the idempotency key is `event_type + resource_id`, so if the exact same event
type legitimately fires twice for the same resource (e.g. a milestone resubmitted after rejection still
produces a second `MILESTONE_SUBMITTED` event on the same milestone id), the second email is treated as
a duplicate and suppressed. This favors "never spam on retries" over covering every resubmission edge
case, which was an acceptable trade-off at this scope.

**API:**
- `GET /api/notifications` — paginated history for the current user.
- `GET /api/notifications/preferences` — per-event email opt-in/out (defaults to enabled).
- `PATCH /api/notifications/preferences` — update preferences.
- `POST /api/notifications/test` — sends a real test email to the current user; disabled when `ENV=production`.

**Testing:** `tests/conftest.py` has an autouse fixture that monkeypatches the Resend call, so the whole
suite (including this module's tests in `tests/test_notifications.py`) never makes a real network call.
`test_notifications.py` covers: success, provider failure (recorded as `FAILED`, request still
succeeds), duplicate-event suppression, preference opt-out, and the production-disabled test endpoint.


1. Build the image

docker build -t freelancer-marketplace .
This installs everything and copies your code in. Takes about 10-15 seconds after the first time (cached).

2. Run the container

docker run -d --name freelancer-api --env-file .env -p 8000:8000 freelancer-marketplace
Breaking down what each part does:

Part	Meaning
-d	run in the background
--name freelancer-api	so you can refer to it later instead of a random ID
--env-file .env	loads your DATABASE_URL, JWT_SECRET, etc. into the container — your .env file itself never gets copied into the image (it's in .dockerignore), so secrets stay out of the built image and only exist at runtime
-p 8000:8000	makes port 8000 inside the container reachable at localhost:8000 on your machine
That's it. On startup the container automatically runs alembic upgrade head (applies any pending migrations) and then starts the API — you don't run those as separate steps.

3. Check it worked

curl http://localhost:8000/health
Should return {"status":"ok"}. Swagger docs are at http://localhost:8000/docs.

Everyday commands you'll actually use

docker logs -f freelancer-api      # watch live logs (including your app's log lines)
docker stop freelancer-api         # stop it
docker start freelancer-api        # start it again (no rebuild needed)
docker rm -f freelancer-api        # stop and remove it completely
After you change code, you need to rebuild before the container picks it up:


docker rm -f freelancer-api
docker build -t freelancer-marketplace .
docker run -d --name freelancer-api --env-file .env -p 8000:8000 freelancer-marketplace
I just ran through all of this for real (build → run → hit /health → hit /docs → both returned 200) to make sure these exact commands work before giving them to you — no docker-compose file exists in this project, so this is genuinely the whole process.




.venv/bin/python -m pytest tests/
