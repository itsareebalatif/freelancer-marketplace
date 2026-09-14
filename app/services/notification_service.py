import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.email_provider import send_email
from app.models.enums import NotificationChannel, NotificationEventType, NotificationStatus
from app.models.notification import NotificationPreference
from app.models.user import User
from app.repositories.notification_repo import NotificationRepository
from app.services.notification_templates import render_template

logger = logging.getLogger(__name__)


def notify(db: Session, user: User, event_type: NotificationEventType, context: dict, *, resource_id) -> None:
    """Create + deliver a notification for a marketplace event.

    Never raises: a provider or delivery failure must not roll back the business
    transaction that already committed before this is called.
    """
    try:
        _notify(db, user, event_type, context, resource_id=resource_id)
    except Exception:
        logger.exception("Notification pipeline failed for event %s on %s", event_type, resource_id)


def _notify(db: Session, user: User, event_type: NotificationEventType, context: dict, *, resource_id) -> None:
    notifications = NotificationRepository(db)
    idempotency_key = f"{event_type.value}:{resource_id}"

    if notifications.get_by_idempotency_key(idempotency_key) is not None:
        logger.info("Skipping duplicate notification for %s", idempotency_key)
        return

    if not _email_enabled(notifications, user.id, event_type):
        notifications.create(
            user_id=user.id,
            event_type=event_type,
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SKIPPED,
            idempotency_key=idempotency_key,
        )
        return

    subject, body = render_template(event_type, context)
    notification = notifications.create(
        user_id=user.id,
        event_type=event_type,
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        subject=subject,
        idempotency_key=idempotency_key,
    )

    try:
        send_email(to=user.email, subject=subject, body=body)
    except Exception as exc:
        logger.warning("Email delivery failed for notification %s: %s", notification.id, exc)
        notifications.update(
            notification,
            status=NotificationStatus.FAILED,
            attempt_count=notification.attempt_count + 1,
            last_error=str(exc)[:500],
        )
        return

    notifications.update(
        notification,
        status=NotificationStatus.SENT,
        attempt_count=notification.attempt_count + 1,
        sent_at=datetime.now(timezone.utc),
    )


def _email_enabled(notifications: NotificationRepository, user_id, event_type: NotificationEventType) -> bool:
    preference: NotificationPreference | None = notifications.get_preference(user_id, event_type)
    return preference is None or preference.email_enabled


def send_test_email(user: User) -> None:
    send_email(
        to=user.email,
        subject="Freelancer Marketplace test notification",
        body="This is a test notification triggered from /api/notifications/test.",
    )


def list_my_notifications(db: Session, user: User, *, page: int, page_size: int):
    return NotificationRepository(db).list_for_user(user.id, page=page, page_size=page_size)


def get_preferences(db: Session, user: User) -> list[NotificationPreference]:
    notifications = NotificationRepository(db)
    existing = {p.event_type: p for p in notifications.list_preferences(user.id)}
    return [
        existing.get(event_type)
        or NotificationPreference(user_id=user.id, event_type=event_type, email_enabled=True)
        for event_type in NotificationEventType
    ]


def update_preferences(db: Session, user: User, updates: list[dict]) -> list[NotificationPreference]:
    notifications = NotificationRepository(db)
    for update in updates:
        notifications.upsert_preference(user.id, update["event_type"], update["email_enabled"])
    return get_preferences(db, user)
