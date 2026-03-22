from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle

from cinepolis_natal_api.exception_handler import standardized_exception_handler


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
    return standardized_exception_handler(exc, context)