import uuid
import pytest
from profiles_app.tasks import send_otp_email, send_profile_creation_event
from unittest.mock import patch


def test_send_otp_email():
    with patch("profiles_app.tasks.send_mail") as mock_send_mail:
        result = send_otp_email("test@example.com", "123456")
        mock_send_mail.assert_called_once()
        assert result["status"] == "sent"
        assert result["email"] == "test@example.com"


def test_send_profile_creation_event():
    # Patch the exact instance variable used in tasks.py
    with patch(
        "profiles_app.tasks._kafka_producer.publish_async"
    ) as mock_publish_async:
        send_profile_creation_event(
            userID=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
        mock_publish_async.assert_called_once()
