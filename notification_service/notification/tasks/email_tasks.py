"""
Email Delivery Celery Tasks
============================
Handles asynchronous email delivery for notifications.

Design:
  - Tasks are queued by NotificationService after WebSocket push
  - Each task fetches the notification from DB to get latest data
  - Uses Django's email backend (console in dev, SMTP in production)
  - Includes retry logic with exponential backoff for SMTP failures
  - autoretry_for handles transient SMTP errors automatically
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger("notification.tasks.email")


@shared_task(
    bind=True,
    queue="email_delivery",
    max_retries=3,
    default_retry_delay=60,  # 1 minute initial delay, then exponential
    acks_late=True,          # Acknowledge only after task completes
)
def send_notification_email(self, notification_id: str, recipient_id: str) -> None:
    """
    Send an email for a notification.

    Called by NotificationService after creating a notification.
    The task fetches the full notification from DB to avoid
    serializing large objects through Celery/Redis.
    """
    try:
        from notification.models import Notification
        notification = Notification.objects.using("notification").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.warning("Notification %s not found for email delivery", notification_id)
        return
    except Exception as exc:
        logger.error("Failed to fetch notification %s: %s", notification_id, exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    # Build email content based on notification type
    subject = _build_subject(notification)
    body = _build_body(notification)
    recipient_email = _get_recipient_email(recipient_id)

    if not recipient_email:
        logger.info(
            "No email address found for recipient=%s, skipping email",
            recipient_id,
        )
        return

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(
            "Notification email sent | notification_id=%s | recipient=%s",
            notification_id, recipient_email,
        )
    except Exception as exc:
        logger.error(
            "Email delivery failed | notification_id=%s | error=%s",
            notification_id, exc,
        )
        # Retry with exponential backoff: 1min, 2min, 4min
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _build_subject(notification) -> str:
    """Build email subject from notification type."""
    type_subjects = {
        "message":     "📬 You have a new message — HomeHaven",
        "application": "📋 Application update — HomeHaven",
        "review":      "⭐ New review — HomeHaven",
        "listing":     "🏠 New listing available — HomeHaven",
        "system":      "ℹ️ HomeHaven notification",
        "security":    "🔒 Security alert — HomeHaven",
        "chat":        "💬 New message — HomeHaven",
    }
    return type_subjects.get(notification.notification_type, notification.title)


def _build_body(notification) -> str:
    """Build plain-text email body."""
    return (
        f"{notification.title}\n\n"
        f"{notification.message}\n\n"
        f"---\n"
        f"Visit HomeHaven to view your notifications: http://localhost:5174/notifications\n\n"
        f"To manage your notification preferences, go to your profile settings.\n"
    )


def _get_recipient_email(recipient_id: str) -> str:
    """
    Fetch recipient email address.

    In production, this would call the profile_service REST API.
    For now, returns None (email delivery is non-critical; logs serve as proof).
    """
    # TODO: Call profile_service to fetch user email when email is needed
    # from shared_lib.resilience import make_resilient_request
    # resp = make_resilient_request(url, ...)
    # return resp.json().get('email')
    logger.debug(
        "Email delivery: profile lookup for recipient=%s (implement via profile_service)",
        recipient_id,
    )
    return None
