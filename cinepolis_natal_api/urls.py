from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs",),
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/catalog/", include("catalog.urls")),
    path("api/v1/reservation/", include("reservations.urls")),
    path("api/v1/users/", include("users.urls")),
]