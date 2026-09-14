from app.models.enums import NotificationEventType
from app.models.notification import Notification, NotificationPreference
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def get_by_idempotency_key(self, key: str) -> Notification | None:
        return self.db.query(Notification).filter(Notification.idempotency_key == key).first()

    def create(self, **fields) -> Notification:
        notification = Notification(**fields)
        return self.add(notification)

    def update(self, notification: Notification, **fields) -> Notification:
        for key, value in fields.items():
            setattr(notification, key, value)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_for_user(self, user_id, *, page: int, page_size: int):
        query = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_preference(self, user_id, event_type: NotificationEventType) -> NotificationPreference | None:
        return (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id, NotificationPreference.event_type == event_type)
            .first()
        )

    def list_preferences(self, user_id) -> list[NotificationPreference]:
        return self.db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).all()

    def upsert_preference(self, user_id, event_type: NotificationEventType, email_enabled: bool) -> NotificationPreference:
        preference = self.get_preference(user_id, event_type)
        if preference is None:
            preference = NotificationPreference(user_id=user_id, event_type=event_type, email_enabled=email_enabled)
            self.db.add(preference)
        else:
            preference.email_enabled = email_enabled
        self.db.commit()
        self.db.refresh(preference)
        return preference
