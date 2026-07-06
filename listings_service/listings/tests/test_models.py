import pytest
from listings.models.unit import Unit
from listings.models.agent import Agent
from django.db.utils import IntegrityError
import uuid


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
def test_unit_creation(agent):
    unit = Unit.objects.create(
        full_address="123 Test St",
        unit_no="1A",
        unit_slug="123-test-st-1a",
        no_bedrooms=2,
        no_bathrooms=1,
        agent_ID=agent,
        building_ID=uuid.uuid4(),
    )
    assert unit.full_address == "123 Test St"
    assert unit.is_furnished is False


@pytest.mark.django_db(databases=["default", "listings"])
def test_unit_constraint_furnished(agent):
    with pytest.raises(IntegrityError):
        Unit.objects.create(
            full_address="123 Test St",
            unit_no="1A",
            unit_slug="123-test-st-1a",
            is_furnished=True,
            is_semi_furnished=True,
            agent_ID=agent,
            building_ID=uuid.uuid4(),
        )
