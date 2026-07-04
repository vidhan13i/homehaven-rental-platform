"""
Celery tasks for chat_service.

Currently implements: offline user notification queuing.
Future support: email, push notification, SMS.

Mirrors the @shared_task pattern from profile_service/profiles_app/tasks.py.
"""
import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger("chat.tasks")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="chat.tasks.notify_offline_user",
    queue="chat_notifications",
)
def notify_offline_user(
    self,
    recipient_id: str,
    message_id: str,
    conversation_id: str,
    sender_username: str,
    preview: str,
) -> dict:
    """
    Deliver a notification to an offline user about a new message.

    Currently logs the notification (foundation for email/push/SMS in production).
    Retries up to 3 times on failure (60s delay between retries).

    Args:
        recipient_id:      UUID string of the offline recipient
        message_id:        UUID string of the new message
        conversation_id:   UUID string of the conversation
        sender_username:   Username of the message sender (may be None)
        preview:           First 100 chars of the message content
    """
    logger.info(
        "Processing offline notification: recipient=%s, message=%s, conversation=%s",
        recipient_id,
        message_id,
        conversation_id,
    )

    try:
        # ── Step 1: Verify message still exists and wasn't deleted ──────────
        from chat.repositories import MessageRepository
        message = MessageRepository.get_by_id(message_id)
        if not message or message.is_deleted:
            logger.info(
                "Skipping notification: message %s no longer exists or was deleted",
                message_id,
            )
            return {"status": "skipped", "reason": "message deleted"}

        # ── Step 2: Check if user came online in the meantime ───────────────
        from chat.services import PresenceService
        if PresenceService.is_online(recipient_id):
            logger.info(
                "Skipping notification: user %s is now online", recipient_id
            )
            return {"status": "skipped", "reason": "user online"}

        # ── Step 3: Deliver notification ─────────────────────────────────────
        # TODO: Implement email, push notification, SMS delivery here.
        # The architecture is ready — just swap the log line below with:
        #   send_email_notification(recipient_id, preview, sender_username)
        #   send_push_notification(recipient_id, preview)
        #   send_sms_notification(recipient_id, preview)

        sender_display = sender_username or "Someone"
        notification_text = (
            f"{sender_display} sent you a message: {preview[:80]}..."
            if len(preview) > 80
            else f"{sender_display} sent you a message: {preview}"
        )

        logger.info(
            "NOTIFICATION [recipient=%s]: %s", recipient_id, notification_text
        )

        return {
            "status": "delivered",
            "recipient_id": recipient_id,
            "conversation_id": conversation_id,
            "notification": notification_text,
        }

    except Exception as exc:
        logger.error(
            "Failed to deliver notification to user %s: %s",
            recipient_id,
            type(exc).__name__,
        )
        raise self.retry(exc=exc)


@shared_task(
    name="chat.tasks.cleanup_presence",
    queue="chat_notifications",
)
def cleanup_presence() -> dict:
    """
    Periodic cleanup task: sync any stale presence records.

    This task should be scheduled via Celery Beat (not implemented here)
    to run every 5 minutes and ensure DB presence records are accurate.
    """
    from chat.repositories import PresenceRepository
    from chat.models import Presence
    from django.utils import timezone
    from datetime import timedelta

    # Mark users offline if their last_seen is more than 2 minutes ago
    cutoff = timezone.now() - timedelta(minutes=2)
    stale_count = Presence.objects.filter(
        online=True,
        last_seen__lt=cutoff,
    ).update(online=False)

    logger.info("Presence cleanup: marked %d stale users as offline", stale_count)
    return {"status": "completed", "cleaned_up": stale_count}
