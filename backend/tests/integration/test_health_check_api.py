import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheckApi:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_health_check_returns_200_when_all_services_are_healthy(
        self,
        api_client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_database",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_redis",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_celery",
            lambda self: "ok",
        )

        response = api_client.get("/health/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "ok",
            "services": {
                "database": "ok",
                "redis": "ok",
                "celery": "ok",
            },
        }

    def test_health_check_returns_503_when_database_is_unavailable(
        self,
        api_client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_database",
            lambda self: "unavailable",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_redis",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_celery",
            lambda self: "ok",
        )

        response = api_client.get("/health/")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {
            "status": "unhealthy",
            "services": {
                "database": "unavailable",
                "redis": "ok",
                "celery": "ok",
            },
        }

    def test_health_check_returns_503_when_redis_is_unavailable(
        self,
        api_client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_database",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_redis",
            lambda self: "unavailable",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_celery",
            lambda self: "ok",
        )

        response = api_client.get("/health/")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {
            "status": "unhealthy",
            "services": {
                "database": "ok",
                "redis": "unavailable",
                "celery": "ok",
            },
        }

    def test_health_check_returns_503_when_celery_is_unavailable(
        self,
        api_client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_database",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_redis",
            lambda self: "ok",
        )
        monkeypatch.setattr(
            "cinepolis_natal_api.health.HealthCheckService._check_celery",
            lambda self: "unavailable",
        )

        response = api_client.get("/health/")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {
            "status": "unhealthy",
            "services": {
                "database": "ok",
                "redis": "ok",
                "celery": "unavailable",
            },
        }