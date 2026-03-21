from django.urls import path

from reservations.views import SessionSeatMapView, TemporarySeatReservationView

urlpatterns = [
    path(
        "sessions/<uuid:session_id>/seats/",
        SessionSeatMapView.as_view(),
        name="session-seat-map",
    ),
    path(
        "sessions/<uuid:session_id>/reservations/",
        TemporarySeatReservationView.as_view(),
        name="temporary-seat-reservation",
    ),
]