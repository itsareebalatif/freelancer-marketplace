import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)


def register(db: Session, data: RegisterRequest) -> User:
    users = UserRepository(db)
    if users.get_by_email(data.email) is not None:
        logger.warning("Registration rejected — email already exists: %s", data.email)
        raise ConflictError("Email is already registered", code="EMAIL_ALREADY_REGISTERED")

    user = users.create(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    logger.info("New user registered: %s (role=%s)", user.id, user.role)
    return user


def _issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token = create_refresh_token()
    RefreshTokenRepository(db).create(user_id=user.id, token=refresh_token)
    return access_token, refresh_token


def login(db: Session, data: LoginRequest) -> tuple[str, str]:
    user = UserRepository(db).get_by_email(data.email)
    if user is None or not verify_password(data.password, user.hashed_password):
        logger.warning("Failed login attempt for %s", data.email)
        raise UnauthorizedError("Incorrect email or password", code="INVALID_CREDENTIALS")

    access_token = create_access_token(user_id=user.id, role=user.role)

    # Reuse an existing, still-valid refresh token instead of minting a new one
    # on every login — logging in again (e.g. re-testing in Swagger) shouldn't
    # spawn a fresh 7-day session each time. A new refresh token is only issued
    # if there's none active yet, or the previous one expired/was revoked
    # (logout, or a rotation via /auth/refresh).
    existing = RefreshTokenRepository(db).get_active_for_user(user.id)
    if existing is not None:
        logger.info("User %s logged in — reusing existing refresh token", user.id)
        return access_token, existing.token

    refresh_token = create_refresh_token()
    RefreshTokenRepository(db).create(user_id=user.id, token=refresh_token)
    logger.info("User %s logged in — issued new refresh token", user.id)
    return access_token, refresh_token


def refresh(db: Session, refresh_token: str) -> tuple[str, str]:
    tokens = RefreshTokenRepository(db)
    stored = tokens.get_by_token(refresh_token)

    if stored is None or stored.is_revoked or stored.expires_at < datetime.now(timezone.utc):
        logger.warning("Rejected refresh token use: invalid, expired, or already used")
        raise UnauthorizedError(
            "Refresh token is invalid, expired, or already used", code="INVALID_REFRESH_TOKEN"
        )

    tokens.revoke(stored)
    user = UserRepository(db).get_by_id(stored.user_id)
    logger.info("Refresh token rotated for user %s", user.id)
    return _issue_tokens(db, user)


def logout(db: Session, user: User) -> None:
    tokens = RefreshTokenRepository(db)
    stored = tokens.get_active_for_user(user.id)
    if stored is not None:
        tokens.revoke(stored)
        logger.info("User %s logged out", user.id)
