import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


@pytest.mark.django_db
class TestAuthenticationAndAuthorizationRules:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="user@example.com",
            username="user",
            password="StrongPass123!",
        )

    def test_register_endpoint_is_public(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "StrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_login_endpoint_is_public(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "user@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_current_user_endpoint_rejects_unauthenticated_requests(self, api_client):
        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_endpoint_rejects_invalid_token(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_endpoint_allows_authenticated_requests(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(user.id)
        assert response.data["email"] == user.email
        assert response.data["username"] == user.username