import pytest
from rest_framework.test import APIClient
from application.models.application import Application
from application.models.applicant import Applicant
from unittest.mock import patch
import uuid


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def applicant():
    return Applicant.objects.create(
        employer="Acme Inc",
        job_title="Software Engineer",
        income=100000,
        savings=5000,
        expected_movein_date="2026-08-01",
        emergency_info={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "relationship": "sister",
        },
    )


@pytest.mark.django_db(databases=["default", "application"])
@patch("shared_lib.kafka.producer.KafkaEventProducer.publish")
def test_create_application(mock_publish, api_client, applicant):
    payload = {
        "unit_ID": str(uuid.uuid4()),
        "building_ID": str(uuid.uuid4()),
        "status": "pending",
        "applicant": str(applicant.id),
    }

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.JWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "user123"})(), None),
    ):
        response = api_client.post("/applications/api/", payload, format="json")
        assert response.status_code == 201
        assert response.data["status"] == "pending"

        # Verify Kafka event was published
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert kwargs["event_type"] == "ApplicationCreated"


@pytest.mark.django_db(databases=["default", "application"])
def test_get_applications(api_client, applicant):
    Application.objects.create(
        unit_ID=uuid.uuid4(),
        building_ID=uuid.uuid4(),
        status="pending",
        applicant=applicant,
    )

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.JWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "user123"})(), None),
    ):
        response = api_client.get("/applications/api/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
