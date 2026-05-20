from django.test import override_settings
from rest_framework.test import APIClient


def _preflight_from(origin):
    client = APIClient()
    return client.options(
        "/api/v1/auth/login/",
        HTTP_ORIGIN=origin,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )


@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
def test_cors_allows_configured_frontend_origin():
    response = _preflight_from("http://localhost:3000")

    assert response["access-control-allow-origin"] == "http://localhost:3000"


@override_settings(CORS_ALLOWED_ORIGINS=["https://app.example.com"])
def test_cors_rejects_origins_not_configured():
    response = _preflight_from("http://localhost:3000")

    assert "access-control-allow-origin" not in response
