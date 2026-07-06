import pytest
from rest_framework.test import APIClient
from reviews.models.reviews import Review
from unittest.mock import patch
import uuid


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@patch("shared_lib.kafka.producer.KafkaEventProducer.publish")
def test_create_review(mock_publish, api_client):
    payload = {
        "unit_ID": str(uuid.uuid4()),
        "building_ID": str(uuid.uuid4()),
        "content": "Great place!",
        "rating": 5,
    }

    with patch(
        "rest_framework.permissions.IsAuthenticated.has_permission", return_value=True
    ), patch(
        "common.authentication.JWTAuthentication.authenticate",
        return_value=(type("User", (), {"id": "user123"})(), None),
    ):
        response = api_client.post("/reviews/api/", payload, format="json")
        assert response.status_code == 201
        assert response.data["rating"] == 5

        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert kwargs["event_type"] == "ReviewCreated"


@pytest.mark.django_db
def test_get_reviews(api_client):
    Review.objects.create(
        user_id="user123",
        unit_ID=uuid.uuid4(),
        building_ID=uuid.uuid4(),
        content="Great place!",
        rating=5,
    )

    response = api_client.get("/reviews/api/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
