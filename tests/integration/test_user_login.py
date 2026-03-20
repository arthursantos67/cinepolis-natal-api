import pytest
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


@pytest.mark.django_db
class TestUserLoginView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="orlando@gmail.com",
            username="pablo2265",
            password="Soueu123*A",
        )

    def test_login_returns_tokens_with_valid_credentials(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "orlando@gmail.com",
                "password": "Soueu123*A",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["access"]
        assert response.data["refresh"]

    def test_login_returns_401_with_invalid_password(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "orlando@gmail.com",
                "password": "wrong-password",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["detail"] == "Invalid credentials."

    def test_login_returns_401_with_unknown_email(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "unknown@gmail.com",
                "password": "Soueu123*A",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["detail"] == "Invalid credentials."

    def test_login_returns_400_with_missing_fields(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "password" in response.data

    def test_login_returns_400_with_invalid_email_format(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "invalid-email",
                "password": "Soueu123*A",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data