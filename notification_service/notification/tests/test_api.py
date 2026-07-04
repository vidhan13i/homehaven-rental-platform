import pytest
from rest_framework.test import APIClient
from notification.models.notification import Notification
from unittest.mock import patch
import uuid

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_notification(api_client):
    payload = {
        "user_id": "user123",
        "title": "Test Alert",
        "message": "This is a test notification",
        "type": "alert"
    }
    
    with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
         patch('common.authentication.JWTAuthentication.authenticate', return_value=(type('User', (), {'id': 'user123'})(), None)):
        response = api_client.post("/notifications/api/", payload, format="json")
        assert response.status_code == 201
        assert response.data["title"] == "Test Alert"

@pytest.mark.django_db
def test_get_notifications(api_client):
    Notification.objects.create(
        user_id="user123",
        title="Test Alert",
        message="This is a test notification",
        type="alert"
    )
    
    with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
         patch('common.authentication.JWTAuthentication.authenticate', return_value=(type('User', (), {'id': 'user123'})(), None)):
        response = api_client.get("/notifications/api/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
