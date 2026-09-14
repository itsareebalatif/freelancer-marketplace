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
│   ├── test_notifications.py     # Notification delivery, retries, idempotency, preferences
│   └── test_attachments.py       # File upload/download/delete authorization and failure cases
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
        ├── notifications.py      # /api/notifications, /api/notifications/preferences, /api/notifications/test
        └── attachments.py        # /api/files (upload, list, metadata, signed download, delete)


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
- `notify(db, user, event_type, context, resource_id=..., background_tasks=...)` is called by business
  services (never by routers) after their own transaction has already committed, so a notification
  problem can never roll back a successful proposal/contract/milestone action.
- Each call first checks the `notifications` table for an existing row with the same
  `idempotency_key` (`"{event_type}:{resource_id}"`). If one exists, the call is a no-op — this is what
  makes retried requests safe from duplicate emails.
- It then checks `notification_preferences` for that user/event; if the user opted out, a `SKIPPED` row
  is recorded and nothing is sent.
- Otherwise it renders the event's template (`app/services/notification_templates.py`) and writes a
  `PENDING` row (with the rendered subject/body stored on it) — this row-creation step is the only part
  that runs inline, and it's a single cheap DB write.
- **Delivery is asynchronous.** Every router that can trigger a notification takes a FastAPI
  `BackgroundTasks` parameter and passes it down to the service call, which passes it to `notify()`.
  `notify()` hands the actual send off via `background_tasks.add_task(deliver_notification, ...)`, so
  the Resend HTTP call happens after the response has already been sent to the client — it never adds
  latency to the request. (If `notify()` is ever called without a `background_tasks` — e.g. a direct
  internal call — it falls back to sending inline rather than silently dropping the notification.)
- **Retries are bounded and failure-aware.** `deliver_notification()` (in the same module) is the
  worker both the background task and the inline fallback use. It opens its own DB session — a
  background task can outlive the request's session, so it can't reuse it — and retries up to
  `MAX_ATTEMPTS = 3` times with a small backoff. Resend errors carry an HTTP-style `code`; a 4xx (other
  than 429 rate-limiting) is treated as **permanent** and fails immediately without retrying (retrying a
  bad request wastes attempts), while 5xx/timeouts/unknown errors are treated as **temporary** and get
  retried. Every attempt updates `attempt_count` and `last_error` on the row, so the final state always
  shows what was actually tried.
- The whole pipeline (`notify()` and `deliver_notification()`) is wrapped so a Resend outage or bug
  never bubbles up into the calling request or crashes the background task silently — failures are
  logged and recorded on the notification row instead.

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
suite never makes a real network call. It also points `notification_service.SessionLocal` at the same
in-memory test database used by the request, since the background worker opens its own session — without
this, delivery in tests would try to hit the real Supabase database instead of the test one.
`test_notifications.py` covers: success, provider failure (recorded as `FAILED`, request still
succeeds), a temporary failure that retries and eventually succeeds, a permanent failure that is not
retried, duplicate-event suppression, preference opt-out, and the production-disabled test endpoint.

**Still not implemented (out of scope for this pass):** SMS delivery — the `channel` column and enum
support it, but no SMS provider (e.g. Twilio) is wired up; only `EMAIL` is ever sent.


## File storage

Secure file upload/download/delete backed by Supabase Storage, generic across every marketplace resource
that can carry an attachment. This replaced the earlier local-disk avatar and contract-document uploads
from Track A, which are now backed by the same system.

**Setup:** create a **private** bucket in the Supabase dashboard (Storage → New bucket → leave "Public
bucket" off) named to match `SUPABASE_STORAGE_BUCKET`. The service role key used here bypasses bucket
policies entirely (it's the same trust boundary as direct DB access), so there's no separate Storage RLS
policy to configure — authorization is enforced entirely in `attachment_service.py`, before any storage
call is made.

**Environment variables** (see `.env.example`):
- `SUPABASE_URL` — your project's URL (`https://<project-ref>.supabase.co`).
- `SUPABASE_SERVICE_ROLE_KEY` — service role key. Never sent to clients; used only server-side to call
  the Storage REST API directly (`app/core/supabase_storage.py`, a thin wrapper — no heavyweight SDK).
- `SUPABASE_STORAGE_BUCKET` — bucket name (default `marketplace-files`).
- `SIGNED_URL_EXPIRY_SECONDS` — how long a download link stays valid (default `300` / 5 minutes). Files
  are never served directly or made public — every read goes through a freshly generated signed URL.

**Data model:** one generic `attachments` table (`app/models/attachment.py`) rather than a table per
resource — `resource_type` (`JOB` / `PROPOSAL` / `CONTRACT` / `MILESTONE` / `PROFILE`) + `resource_id`
polymorphically associates a file with any of them. Columns: `owner_id` (uploader), `original_filename`
(display only), `storage_key` (the actual bucket path — never returned by the API), `mime_type`,
`size_bytes`, `checksum` (SHA-256), timestamps.

**Authorization (`app/services/attachment_service.py`):** `_resolve_participants()` maps a resource to
the user ids allowed to touch its files — a job's client, a proposal's freelancer + the job's client, a
contract/milestone's client + freelancer, or a profile's own owner. Every upload/list/get/download call
checks the requester is in that set, *not* just that they're logged in. Delete is narrower still —
restricted to the uploader, so one contract party can't delete a file the other party uploaded as
evidence in a dispute.

**Controlled storage paths:** the storage key is generated entirely server-side —
`{resource_type}/{resource_id}/{uuid4().hex}{extension}` — where the extension comes from a fixed
MIME-type lookup, not the client's filename. The original filename is kept only as display metadata and
never touches the path, so there's no path-traversal surface to sanitize against.

**Validation:** 5MB max, read in 1MB chunks so an oversized upload is rejected without buffering the
whole thing into memory first. Allowed types differ by resource — profile avatars must be an image
(`jpeg`/`png`/`webp`); job/proposal/contract/milestone attachments accept those plus `pdf`.

**Duplicate uploads:** the same file (by SHA-256, scoped to one resource) re-uploaded returns the
existing attachment row instead of writing a second copy to storage — enforced by a unique constraint on
`(resource_type, resource_id, checksum)`, with a race against a concurrent identical upload handled by
catching the constraint violation and returning the row that won.

**Consistency on partial failure:** upload writes to storage first, then inserts the DB row; if the DB
insert fails after a successful storage write, the just-uploaded object is deleted to avoid an orphan.
Delete does the reverse — the storage object is removed first, and the DB row is only deleted if that
succeeds; if storage delete fails, the row is kept (visible, red-flagged by a `409`) rather than silently
pointing at a file that may or may not still exist.

**Deleting a resource:** none of the marketplace resources (jobs, proposals, contracts, milestones) have
a delete endpoint in this app, so "what happens to attachments when the resource is deleted" doesn't
currently apply — if resource deletion is added later, its attachments should be removed through
`attachment_service.delete_attachment()` for each one rather than a DB-level cascade, since storage
cleanup needs an API call, not just a row delete.

**API:**
- `POST /api/files?resource_type=&resource_id=` — multipart upload.
- `GET /api/files?resource_type=&resource_id=` — list attachments on a resource.
- `GET /api/files/{id}` — metadata only.
- `GET /api/files/{id}/download` — a fresh signed URL (`{url, expires_in}`), not a redirect or proxied
  bytes.
- `DELETE /api/files/{id}` — uploader only.

**Testing:** `tests/conftest.py` has an autouse `mock_storage` fixture (an in-memory dict standing in for
the bucket) so the suite never calls Supabase. `test_attachments.py` covers: upload/list by an authorized
participant, a non-participant blocked from upload/list, unauthenticated access, cross-user access to
another freelancer's profile file and to an unrelated contract's files, an invalid file type, an avatar
rejecting a non-image, an oversized file, a missing attachment (404 on get/download/delete), duplicate
upload reuse, a signed-URL download response, delete-then-404, a non-uploader participant blocked from
deleting, a simulated storage failure on upload (no orphan row) and on delete (row kept), and uploading
to a resource that doesn't exist.

**Verified live** against the real Supabase project: uploaded a file, fetched it through the signed URL
(200, correct bytes), confirmed the same object with no token returns 400 (bucket is genuinely private,
not just "hidden"), then deleted it and confirmed the metadata 404s afterward.


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
