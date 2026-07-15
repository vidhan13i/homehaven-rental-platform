import pytest
from rest_framework.test import APIClient
from notification.models.notification import Notification
from unittest.mock import patch
import uuid


@pytest.fixture
def api_client():
    return APIClient()


MOCK_USER_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.django_db(databases=["default", "notification"])
def test_create_notification(api_client):
    payload = {
        "title": "Test Alert",
        "message": "This is a test notification",
        "notification_type": "system",
        "recipient_id": MOCK_USER_ID,
    }

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "notification.authentication.http.TrustedJWTAuthentication.authenticate",
        return_value=(
            type("User", (), {"id": MOCK_USER_ID})(),
            None,
        ),
    ):
        response = api_client.post("/api/notifications/list/", payload, format="json")
        assert response.status_code == 201
        assert response.data["title"] == "Test Alert"


@pytest.mark.django_db(databases=["default", "notification"])
def test_get_notifications(api_client):
    Notification.objects.create(
        recipient_id=uuid.UUID(MOCK_USER_ID),
        title="Test Alert",
        message="This is a test notification",
        notification_type="system",
    )

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "notification.authentication.http.TrustedJWTAuthentication.authenticate",
        return_value=(
            type("User", (), {"id": MOCK_USER_ID})(),
            None,
        ),
    ):
        response = api_client.get("/api/notifications/list/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
