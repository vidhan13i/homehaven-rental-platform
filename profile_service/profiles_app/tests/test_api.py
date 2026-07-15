import uuid
import pytest
from rest_framework.test import APIClient
from profiles_app.models import Profile
from unittest.mock import patch


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db(databases=["default", "profiles_app"])
@patch("profiles_app.tasks.send_profile_creation_event")
def test_create_profile(mock_send_event, api_client):
    payload = {
        "userID": "11111111-1111-1111-1111-111111111111",
        "first_name": "Test",
        "last_name": "Profile",
        "email": "test@example.com",
        "DOB": "1990-01-01",
        "gender": "M",
    }

    # Mock auth to bypass JWT verification for unit tests

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "11111111-1111-1111-1111-111111111111"})(), None),
    ):
        response = api_client.post("/api/profiles/profiles/", payload, format="json")
        assert response.status_code == 201
        assert response.data["first_name"] == "Test"
        mock_send_event.delay.assert_called_once()
@pytest.mark.django_db(databases=["default", "profiles_app"])
def test_get_profile(api_client):
    profile = Profile.objects.create(
            userID=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            first_name="Test",
            last_name="Profile",
            email="test@example.com",
            DOB="1990-01-01",
            gender="M",)

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "11111111-1111-1111-1111-111111111111"})(), None),
    ):
        response = api_client.get(f"/api/profiles/profiles/{profile.id}/")
        assert response.status_code == 200
        assert response.data["email"] == "test@example.com"
