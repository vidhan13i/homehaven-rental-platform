import pytest
from rest_framework.test import APIClient
from listings.models.unit import Unit
from listings.models.agent import Agent
from unittest.mock import patch
import uuid


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def agent():
    return Agent.objects.create(
        first_name="Test",
        last_name="Agent",
        email="agent@test.com",
        phone_number=1234567890,
        agent_organization="Test Realty",
    )


@pytest.mark.django_db(databases=["default", "listings"])
def test_list_units(api_client, agent):
    Unit.objects.create(
        full_address="123 Test St",
        unit_no="1A",
        unit_slug="123-test-st-1a",
        no_bedrooms=2,
        no_bathrooms=1,
        agent_ID=agent,
        building_ID=uuid.uuid4(),
    )

    response = api_client.get("/listings/units/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["full_address"] == "123 Test St"


@pytest.mark.django_db(databases=["default", "listings"])
def test_create_unit(api_client, agent):
    payload = {
        "full_address": "456 New St",
        "unit_no": "2B",
        "unit_slug": "456-new-st-2b",
        "no_bedrooms": 3,
        "no_bathrooms": 2,
        "agent_ID": str(agent.id),
        "building_ID": str(uuid.uuid4()),
    }

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.JWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "user123"})(), None),
    ):
        response = api_client.post("/listings/units/", payload, format="json")
        assert response.status_code == 201
        assert response.data["full_address"] == "456 New St"
