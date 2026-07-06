import pytest
from rest_framework.test import APIClient
from reviews.models.reviews import Review
from unittest.mock import patch
import uuid


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

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.TrustedJWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "user123"})(), None),
    ):
        response = api_client.post("/reviews/api/", payload, format="json")
        assert response.status_code == 201
        assert response.data["Title"] == "Great place"

        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert kwargs["event_type"] == "ReviewCreated"


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

    response = api_client.get("/reviews/api/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
