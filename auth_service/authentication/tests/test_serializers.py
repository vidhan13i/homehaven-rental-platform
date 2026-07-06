import pytest
from authentication.serializers import RegisterSerializer, UserSerializer
from authentication.models import User


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_user_serializer():
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
        first_name="Test",
        last_name="User",
    )
    serializer = UserSerializer(user)
    data = serializer.data
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert "password" not in data


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_register_serializer_valid():
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "strongpassword123",
        "first_name": "New",
        "last_name": "User",
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid()
    user = serializer.save()
    assert user.username == "newuser"
    assert user.check_password("strongpassword123")


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_register_serializer_duplicate_email():
    User.objects.create_user(
        username="existing", email="duplicate@example.com", password="pwd"
    )
    data = {
        "username": "newuser",
        "email": "duplicate@example.com",
        "password": "strongpassword123",
        "first_name": "New",
        "last_name": "User",
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "A user with this email already exists." in str(serializer.errors["email"])
