import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from application.models.application import Application
from application.models.applicant import Applicant


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
            "phone": "5551234",
            "relationship": "sister",
        },
    )


@pytest.mark.django_db(databases=["default", "application"])
@patch("shared_lib.kafka.producer.KafkaEventProducer.publish")
def test_create_application(mock_publish, api_client, applicant):
    payload = {
        "unit_ID": str(uuid.uuid4()),
        "building_ID": str(uuid.uuid4()),
        "applicant_ID": applicant.id,
        "lease_term": "12 months",
        "resident_info": {
            "name": "John Doe",
            "gender": "male",
            "dob": "2000-01-01",
        },
    }

    url = reverse("application-list")

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission",
        return_value=True,
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": applicant.profile_ID})(), None),
    ):
        response = api_client.post(
            url,
            payload,
            format="json",
        )

    assert response.status_code == 201
    assert response.data["applicant_ID"] == applicant.id
    assert response.data["lease_term"] == "12 months"
    assert response.data["application_status"] == Application.ApplicationStatus.DRAFT

    mock_publish.assert_called_once()


@pytest.mark.django_db(databases=["default", "application"])
def test_get_applications(api_client, applicant):
    Application.objects.create(
        unit_ID=uuid.uuid4(),
        building_ID=uuid.uuid4(),
        applicant_ID=applicant,
        lease_term="12 months",
        resident_info={
            "name": "John Doe",
            "gender": "male",
            "dob": "2000-01-01",
        },
        application_status=Application.ApplicationStatus.DRAFT,
    )

    url = reverse("application-list")

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission",
        return_value=True,
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": applicant.profile_ID})(), None),
    ):
        response = api_client.get(url)

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
