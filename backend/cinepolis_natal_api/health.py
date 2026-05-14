from celery import current_app
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError


class HealthCheckService:
    def execute(self) -> dict:
        services = {
            "database": self._check_database(),
            "redis": self._check_redis(),
            "celery": self._check_celery(),
        }

        overall_status = "ok" if all(
            status == "ok" for status in services.values()
        ) else "unhealthy"

        return {
            "status": overall_status,
            "services": services,
        }

    def _check_database(self) -> str:
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return "ok"
        except OperationalError:
            return "unavailable"
        except Exception:
            return "unavailable"

    def _check_redis(self) -> str:
        try:
            cache.set("healthcheck:ping", "pong", timeout=5)
            value = cache.get("healthcheck:ping")
            return "ok" if value == "pong" else "unavailable"
        except Exception:
            return "unavailable"

    def _check_celery(self) -> str:
        try:
            inspect = current_app.control.inspect(timeout=1.0)
            response = inspect.ping()
            return "ok" if response else "unavailable"
        except Exception:
            return "unavailable"