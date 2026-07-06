"""
Celery tasks for profile_service.

All tasks use @shared_task so they work correctly whether Celery
is running as a standalone worker or imported in tests.
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

from shared_lib.kafka.producer import KafkaEventProducer
from shared_lib.kafka.events import build_event
from shared_lib.kafka.topics import Topics

_kafka_producer = KafkaEventProducer()


@shared_task(name="profiles_app.tasks.send_profile_creation_event")
def send_profile_creation_event(
    user_id: str, email: str, first_name: str, last_name: str
) -> None:
    """Publish a ProfileCreated domain event to Kafka (fire-and-forget)."""
    event = build_event(
        event_type="ProfileCreated",
        aggregate_id=str(user_id),
        source_service="profile_service",
        payload={
            "user_id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    _kafka_producer.publish_async(Topics.PROFILE_CREATED, event, key=str(user_id))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # retry after 60s on failure
    name="profiles_app.tasks.send_otp_email",
)
def send_otp_email(self, email: str, otp: str) -> dict:
    """
    Send a 6-digit OTP to the user's email address.

    Retries up to 3 times (60s delay) if the SMTP call fails.
    The OTP is passed as a plain string — it is never stored in
    the task payload in persistent storage beyond the broker TTL.

    Args:
        email: Recipient email address.
        otp:   Plain-text 6-digit OTP code.

    Returns:
        dict with 'status' key.
    """
    subject = "Your Haven verification code"
    message = (
        f"Hi,\n\n"
        f"Your one-time verification code is:\n\n"
        f"    {otp}\n\n"
        f"This code expires in 5 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"— Haven Rentals"
    )
    html_message = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 480px; margin: 0 auto; padding: 40px 20px;">
        <div style="background: #111418; border-radius: 16px; padding: 40px; text-align: center;">
            <h1 style="color: #e8eaed; font-size: 22px; margin: 0 0 8px;">Verify your email</h1>
            <p style="color: #9aa0a6; font-size: 14px; margin: 0 0 32px;">
                Enter this code in the Haven app. It expires in <strong>5 minutes</strong>.
            </p>
            <div style="background: #1a1d22; border: 1px solid #2a2d33; border-radius: 12px;
                        padding: 24px; letter-spacing: 0.5em; font-size: 32px;
                        font-weight: 700; color: #f59e0b;">
                {otp}
            </div>
            <p style="color: #5f6368; font-size: 12px; margin: 24px 0 0;">
                If you didn&rsquo;t create a Haven account, ignore this email.
            </p>
        </div>
    </div>
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        # IMPORTANT: never log the OTP value itself in production
        logger.info("OTP email dispatched to %s", email)
        return {"status": "sent", "email": email}

    except Exception as exc:
        logger.error("Failed to send OTP email to %s: %s", email, type(exc).__name__)
        # Retry with exponential backoff
        raise self.retry(exc=exc)
