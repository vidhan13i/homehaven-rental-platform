import pytest
from authentication.models import User


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_user_creation():
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
        first_name="Test",
        last_name="User",
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert str(user) == "testuser (test@example.com)"
    assert user.check_password("securepassword123")
