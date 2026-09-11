import logging
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.Session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        logger.warning("Rejected access token: %s", exc)
        raise UnauthorizedError("Invalid or expired access token", code="INVALID_ACCESS_TOKEN")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise UnauthorizedError("Invalid or expired access token", code="INVALID_ACCESS_TOKEN")

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        logger.warning("Access token valid but user %s no longer exists", payload["sub"])
        raise UnauthorizedError("User no longer exists", code="USER_NOT_FOUND")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    return get_current_user(credentials, db)


def require_role(role: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            logger.warning(
                "User %s (role=%s) denied — %s required", current_user.id, current_user.role, role
            )
            role_name = role.value if hasattr(role, "value") else role
            raise ForbiddenError(f"This action requires the {role_name} role", code="ROLE_NOT_ALLOWED")
        return current_user

    return checker
