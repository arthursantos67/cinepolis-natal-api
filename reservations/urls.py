from django.urls import path

from reservations.views import SessionSeatMapView

urlpatterns = [
    path(
        "sessions/<uuid:session_id>/seats/",
        SessionSeatMapView.as_view(),
        name="session-seat-map",
    ),
]