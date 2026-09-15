from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.enums import NotificationEventType

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=select_autoescape(["html"]))


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


# Subjects are plain text (no HTML needed), so they stay simple format strings.
# The body is a full HTML template — the file name below matches the event's
# lowercased name under app/templates/email/.
SUBJECTS = {
    NotificationEventType.USER_REGISTERED: "Welcome to Freelancer Marketplace",
    NotificationEventType.PROPOSAL_RECEIVED: 'New proposal on your job "{job_title}"',
    NotificationEventType.PROPOSAL_ACCEPTED: "Your proposal was accepted",
    NotificationEventType.PROPOSAL_REJECTED: "Your proposal was not selected",
    NotificationEventType.CONTRACT_CREATED: "New contract created",
    NotificationEventType.MILESTONE_SUBMITTED: "Milestone submitted for review",
    NotificationEventType.MILESTONE_APPROVED: "Milestone approved",
    NotificationEventType.MILESTONE_REJECTED: "Milestone rejected",
    NotificationEventType.CONTRACT_COMPLETED: "Contract completed",
    NotificationEventType.REVIEW_RECEIVED: "You received a new review",
}


def render_template(event_type: NotificationEventType, context: dict) -> tuple[str, str]:
    subject = SUBJECTS[event_type].format_map(_SafeDict(context))
    template = _env.get_template(f"{event_type.value.lower()}.html")
    html = template.render(**context)
    return subject, html
