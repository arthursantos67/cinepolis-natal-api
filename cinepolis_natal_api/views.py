from django.http import JsonResponse

from .health import HealthCheckService


def health_check(request):
    result = HealthCheckService().execute()
    status_code = 200 if result["status"] == "ok" else 503
    return JsonResponse(result, status=status_code)