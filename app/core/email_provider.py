import resend

from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


def send_email(*, to: str, subject: str, body: str) -> None:
    """`body` is rendered HTML (see app/services/notification_templates.py)."""
    resend.Emails.send({
        "from": settings.EMAIL_FROM_ADDRESS,
        "to": [to],
        "subject": subject,
        "html": body,
    })
