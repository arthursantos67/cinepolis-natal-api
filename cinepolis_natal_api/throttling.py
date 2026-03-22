from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle, UserRateThrottle
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class GlobalAnonRateThrottle(AnonRateThrottle):
    scope = "anon"


class GlobalUserRateThrottle(UserRateThrottle):
    scope = "user"


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        return self.get_ident(request)


class ReservationRateThrottle(SimpleRateThrottle):
    scope = "reservation"

    def get_cache_key(self, request, view):
        return self.get_ident(request)


def throttling_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        wait = None
        if hasattr(exc, "wait"):
            wait = exc.wait

        message = "Request limit exceeded. Please try again later."
        if wait:
            message = f"Request limit exceeded. Please try again in {int(wait)} seconds."

        return Response(
            {
                "error": {
                    "code": "THROTTLED",
                    "message": message,
                    "status": status.HTTP_429_TOO_MANY_REQUESTS,
                }
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    return response