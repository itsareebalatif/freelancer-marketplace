from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import hash_token
from app.models.user import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository):
    def create(self, *, user_id, token: str) -> RefreshToken:
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = RefreshToken(user_id=user_id, token_hash=hash_token(token), expires_at=expires_at)
        return self.add(refresh_token)

    def get_by_token(self, token: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(token)).first()

    def get_active_for_user(self, user_id) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshToken.created_at.desc())
            .first()
        )

    def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.is_revoked = True
        self.db.commit()
