import pytest
from rest_framework.test import APIClient
from authentication.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_register_api(api_client):
    payload = {
        "username": "apiuser",
        "email": "api@example.com",
        "password": "securepassword123",
        "first_name": "API",
        "last_name": "User",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    assert response.data["user"]["username"] == "apiuser"
    assert "token" in response.data


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_login_api_success(api_client):
    User.objects.create_user(
        username="loginuser",
        email="login@example.com",
        password="securepassword123",
        first_name="Login",
        last_name="User",
    )
    payload = {"username": "loginuser", "password": "securepassword123"}
    response = api_client.post("/api/auth/login/", payload, format="json")
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["username"] == "loginuser"


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_login_api_failure(api_client):
    User.objects.create_user(
        username="loginuser", email="login@example.com", password="securepassword123"
    )
    payload = {"username": "loginuser", "password": "wrongpassword"}
    response = api_client.post("/api/auth/login/", payload, format="json")
    assert response.status_code == 401
    assert "error" in response.data


@pytest.mark.django_db(databases=["default", "auth_db"])
def test_validate_token_api(api_client):
    user = User.objects.create_user(
        username="validuser", email="valid@example.com", password="securepassword123"
    )
    # Login to get token
    login_response = api_client.post(
        "/api/auth/login/",
        {"username": "validuser", "password": "securepassword123"},
        format="json",
    )

    token = login_response.data["access"]

    # Validate token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    validate_response = api_client.get("/api/auth/validate-token/")
    assert validate_response.status_code == 200
    assert validate_response.data["valid"] is True
    assert validate_response.data["user"]["username"] == "validuser"
