from itertools import count

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

_ip_counter = count(1)


@pytest.mark.django_db
class TestUserLoginView:
    @pytest.fixture
    def api_client(self):
        client = APIClient()
        client.defaults["REMOTE_ADDR"] = f"10.20.30.{next(_ip_counter)}"
        return client

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

    def test_token_refresh_returns_new_access_token(self, api_client, user):
        login_response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": "orlando@gmail.com",
                "password": "Soueu123*A",
            },
            format="json",
        )

        refresh_response = api_client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.data
        assert "refresh" not in refresh_response.data

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh_response.data['access']}"
        )
        current_user_response = api_client.get("/api/v1/users/me/")

        assert current_user_response.status_code == status.HTTP_200_OK
        assert current_user_response.data["id"] == str(user.id)

    def test_token_refresh_returns_standard_error_with_invalid_refresh(
        self,
        api_client,
    ):
        response = api_client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": "invalid-refresh-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"]["code"] == "NOT_AUTHENTICATED"
        assert response.data["error"]["status"] == 401
        assert isinstance(response.data["error"]["details"], dict)

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
        assert response.data["error"]["code"] == "INVALID_CREDENTIALS"
        assert response.data["error"]["status"] == 401
        assert response.data["error"]["message"] == "Invalid credentials."

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
        assert response.data["error"]["code"] == "INVALID_CREDENTIALS"
        assert response.data["error"]["status"] == 401
        assert response.data["error"]["message"] == "Invalid credentials."

    def test_login_returns_400_with_missing_fields(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"]["code"] == "VALIDATION_FAILED"
        assert response.data["error"]["status"] == 400
        assert "email" in response.data["error"]["details"]
        assert "password" in response.data["error"]["details"]

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
        assert response.data["error"]["code"] == "VALIDATION_FAILED"
        assert response.data["error"]["status"] == 400
        assert "email" in response.data["error"]["details"]
