import pytest
from rest_framework.test import APIClient
from building.models.building import Building
from unittest.mock import patch

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_building(api_client):
    payload = {
        "name": "Test Building",
        "address": "123 Test Ave",
        "slug": "test-building",
        "city": "Test City",
        "state": "TS"
    }
    
    with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True), \
         patch('common.authentication.JWTAuthentication.authenticate', return_value=(type('User', (), {'id': 'user123'})(), None)):
        response = api_client.post("/buildings/api/", payload, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Test Building"

@pytest.mark.django_db
def test_get_building(api_client):
    building = Building.objects.create(
        name="Test Building",
        address="123 Test Ave",
        slug="test-building",
        city="Test City",
        state="TS"
    )
    
    response = api_client.get("/buildings/api/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Test Building"
