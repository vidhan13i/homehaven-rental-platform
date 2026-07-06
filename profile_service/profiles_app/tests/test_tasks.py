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
    with patch("shared_lib.kafka.producer.KafkaEventProducer") as mock_producer_class:
        send_profile_creation_event(
            user_id="user123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
        mock_producer_class.return_value.publish.assert_called_once()
