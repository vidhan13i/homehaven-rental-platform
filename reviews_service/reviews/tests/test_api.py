import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from reviews.models.reviews import Review


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db(databases=["default", "reviews"])
@patch("shared_lib.kafka.producer.KafkaEventProducer.publish")
def test_create_review(mock_publish, api_client):
    payload = {
        "profile_ID": str(uuid.uuid4()),
        "building_ID": str(uuid.uuid4()),
        "full_address": "123 Test St",
        "cleanliness_rating": 5.0,
        "garbage_management_rating": 4.5,
        "neighbours_rating": 4.0,
        "water_supply_rating": 5.0,
        "building_maintenance_rating": 4.0,
        "Title": "Great place",
        "Pros": "Everything",
        "Cons": "Nothing",
        "Advice": "Rent here",
        "move_in_date": "2022-01-01",
        "move_out_date": "2023-01-01",
    }

    url = reverse("reviews_api:review-list")

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission",
        return_value=True,
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": uuid.UUID("11111111-1111-1111-1111-111111111111")})(), None),
    ):
        response = api_client.post(url, payload, format="json")

    assert response.status_code == 201
    assert response.data["Title"] == "Great place"

    mock_publish.assert_called_once()


@pytest.mark.django_db(databases=["default", "reviews"])
def test_get_reviews(api_client):
    Review.objects.create(
        profile_ID=uuid.uuid4(),
        building_ID=uuid.uuid4(),
        full_address="123 Test St",
        cleanliness_rating=5.0,
        garbage_management_rating=4.5,
        neighbours_rating=4.0,
        water_supply_rating=5.0,
        building_maintenance_rating=4.0,
        Title="Great place",
        Pros="Everything",
        Cons="Nothing",
        Advice="Rent here",
        move_in_date="2022-01-01",
        move_out_date="2023-01-01",
    )

    url = reverse("reviews_api:review-list")

    response = api_client.get(url)

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
