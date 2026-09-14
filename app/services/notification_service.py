import logging
import time
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.email_provider import send_email
from app.db.Session import SessionLocal
from app.models.enums import NotificationChannel, NotificationEventType, NotificationStatus
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.repositories.notification_repo import NotificationRepository
from app.services.notification_templates import render_template

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.2


def notify(
    db: Session,
    user: User,
    event_type: NotificationEventType,
    context: dict,
    *,
    resource_id,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    """Create + schedule delivery of a notification for a marketplace event.

    Never raises: a provider or delivery failure must not roll back the business
    transaction that already committed before this is called. Row creation is
    synchronous (cheap, same request's db session); the actual send is handed to
    `background_tasks` so it doesn't add provider latency to the API response —
    falling back to an inline send when no background_tasks is given (e.g. a
    direct/internal call).
    """
    try:
        _notify(db, user, event_type, context, resource_id=resource_id, background_tasks=background_tasks)
    except Exception:
        logger.exception("Notification pipeline failed for event %s on %s", event_type, resource_id)


def _notify(
    db: Session,
    user: User,
    event_type: NotificationEventType,
    context: dict,
    *,
    resource_id,
    background_tasks: BackgroundTasks | None,
) -> None:
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
        body=body,
        idempotency_key=idempotency_key,
    )

    if background_tasks is not None:
        background_tasks.add_task(deliver_notification, notification.id)
    else:
        deliver_notification(notification.id)


def _email_enabled(notifications: NotificationRepository, user_id, event_type: NotificationEventType) -> bool:
    preference: NotificationPreference | None = notifications.get_preference(user_id, event_type)
    return preference is None or preference.email_enabled


def _is_permanent_failure(exc: Exception) -> bool:
    """4xx (other than 429 rate-limit) means the request itself is bad — retrying
    won't help. Everything else (5xx, timeouts, network errors) is treated as
    temporary and worth retrying."""
    code = getattr(exc, "code", None)
    try:
        code = int(code)
    except (TypeError, ValueError):
        return False
    return 400 <= code < 500 and code != 429


def deliver_notification(notification_id) -> None:
    """Worker that actually calls the email provider. Runs either inline or as a
    FastAPI background task — either way it opens its own DB session rather than
    reusing the caller's, since a background task can outlive the request's session.
    """
    db = SessionLocal()
    try:
        notifications = NotificationRepository(db)
        notification = db.get(Notification, notification_id)
        if notification is None or notification.status == NotificationStatus.SENT:
            return

        user = db.get(User, notification.user_id)
        if user is None:
            notifications.update(
                notification, status=NotificationStatus.FAILED, last_error="Recipient no longer exists"
            )
            return

        last_error = None
        for attempt in range(notification.attempt_count + 1, MAX_ATTEMPTS + 1):
            try:
                send_email(to=user.email, subject=notification.subject, body=notification.body)
            except Exception as exc:
                last_error = str(exc)[:500]
                permanent = _is_permanent_failure(exc)
                logger.warning(
                    "Email delivery attempt %d/%d failed for notification %s (%s): %s",
                    attempt,
                    MAX_ATTEMPTS,
                    notification.id,
                    "permanent" if permanent else "temporary",
                    exc,
                )
                notification = notifications.update(
                    notification, status=NotificationStatus.FAILED, attempt_count=attempt, last_error=last_error
                )
                if permanent:
                    return
                if attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue

            notifications.update(
                notification,
                status=NotificationStatus.SENT,
                attempt_count=attempt,
                sent_at=datetime.now(timezone.utc),
            )
            return

        logger.error(
            "Notification %s exhausted %d attempts, giving up: %s", notification.id, MAX_ATTEMPTS, last_error
        )
    finally:
        db.close()


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
