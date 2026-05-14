from django.urls import path

from reservations.views import (
    CheckoutView,
    SeatDetailView,
    SeatListCreateView,
    SeatRowDetailView,
    SeatRowListCreateView,
    SessionSeatDetailView,
    SessionSeatListCreateView,
    SessionSeatMapView,
    TicketDetailView,
    TicketListCreateView,
    TemporarySeatReservationView,
)

urlpatterns = [
    path("seat-rows/", SeatRowListCreateView.as_view(), name="seat-row-list-create"),
    path("seat-rows/<uuid:pk>/", SeatRowDetailView.as_view(), name="seat-row-detail"),
    path("seats/", SeatListCreateView.as_view(), name="seat-list-create"),
    path("seats/<uuid:pk>/", SeatDetailView.as_view(), name="seat-detail"),
    path(
        "session-seats/",
        SessionSeatListCreateView.as_view(),
        name="session-seat-list-create",
    ),
    path(
        "session-seats/<uuid:pk>/",
        SessionSeatDetailView.as_view(),
        name="session-seat-detail",
    ),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("tickets/<uuid:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("sessions/<uuid:session_id>/seats/", SessionSeatMapView.as_view(), name="session-seat-map"),
    path("sessions/<uuid:session_id>/reservations/", TemporarySeatReservationView.as_view(), name="temporary-seat-reservation"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
]