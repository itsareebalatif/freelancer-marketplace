from app.models.enums import NotificationEventType


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


TEMPLATES = {
    NotificationEventType.USER_REGISTERED: (
        "Welcome to Freelancer Marketplace",
        "Hi {full_name},\n\nYour account has been created successfully. You can now start "
        "posting jobs or submitting proposals.\n\n Freelancer Marketplace",
    ),
    NotificationEventType.PROPOSAL_RECEIVED: (
        "New proposal on your job \"{job_title}\"",
        "Hi {client_name},\n\n{freelancer_name} submitted a proposal for your job "
        "\"{job_title}\".\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.PROPOSAL_ACCEPTED: (
        "Your proposal was accepted",
        "Hi {freelancer_name},\n\nYour proposal for \"{job_title}\" was accepted. A contract "
        "has been created.\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.PROPOSAL_REJECTED: (
        "Your proposal was not selected",
        "Hi {freelancer_name},\n\nYour proposal for \"{job_title}\" was not selected this "
        "time.\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.CONTRACT_CREATED: (
        "New contract created",
        "Hi {freelancer_name},\n\nA contract for \"{job_title}\" is now active.\n\n"
        "— Freelancer Marketplace",
    ),
    NotificationEventType.MILESTONE_SUBMITTED: (
        "Milestone submitted for review",
        "Hi {client_name},\n\nThe milestone \"{milestone_title}\" has been submitted for your "
        "review.\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.MILESTONE_APPROVED: (
        "Milestone approved",
        "Hi {freelancer_name},\n\nYour milestone \"{milestone_title}\" was approved.\n\n"
        "— Freelancer Marketplace",
    ),
    NotificationEventType.MILESTONE_REJECTED: (
        "Milestone rejected",
        "Hi {freelancer_name},\n\nYour milestone \"{milestone_title}\" was rejected. Please "
        "review the feedback and resubmit.\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.CONTRACT_COMPLETED: (
        "Contract completed",
        "Hi {freelancer_name},\n\nThe contract for \"{job_title}\" has been marked "
        "completed.\n\n— Freelancer Marketplace",
    ),
    NotificationEventType.REVIEW_RECEIVED: (
        "You received a new review",
        "Hi {reviewee_name},\n\nYou received a {rating}-star review: \"{comment}\"\n\n"
        "— Freelancer Marketplace",
    ),
}


def render_template(event_type: NotificationEventType, context: dict) -> tuple[str, str]:
    subject, body = TEMPLATES[event_type]
    safe_context = _SafeDict(context)
    return subject.format_map(safe_context), body.format_map(safe_context)
