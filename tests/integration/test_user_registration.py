import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_user_registration_succeeds():
    client = APIClient()

    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "StrongPassword123",
    }

    response = client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 201
    assert response.data["email"] == payload["email"]
    assert response.data["username"] == payload["username"]
    assert "password" not in response.data

    user = User.objects.get(email=payload["email"])
    assert user.username == payload["username"]
    assert user.check_password(payload["password"])
    assert str(user.password) != payload["password"]


@pytest.mark.django_db
def test_user_registration_rejects_duplicate_email():
    User.objects.create_user(
        email="duplicate@example.com",
        username="existinguser",
        password="StrongPassword123",
    )

    client = APIClient()

    payload = {
        "email": "duplicate@example.com",
        "username": "newusername",
        "password": "StrongPassword123",
    }

    response = client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_user_registration_rejects_duplicate_username():
    User.objects.create_user(
        email="existing@example.com",
        username="duplicateuser",
        password="StrongPassword123",
    )

    client = APIClient()

    payload = {
        "email": "new@example.com",
        "username": "duplicateuser",
        "password": "StrongPassword123",
    }

    response = client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 400
    assert "username" in response.data


@pytest.mark.django_db
def test_user_registration_requires_email_username_and_password():
    client = APIClient()

    response = client.post("/api/v1/auth/register/", {}, format="json")

    assert response.status_code == 400
    assert "email" in response.data
    assert "username" in response.data
    assert "password" in response.data