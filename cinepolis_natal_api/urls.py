from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/catalog/", include("catalog.urls")),
    path("api/v1/reservation/", include("reservations.urls")),
]