import pytest
from datetime import timedelta

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Movie, Room, Session
from reservations.models import Seat, SeatRow, SessionSeat, SessionSeatStatus
from reservations.views import (
    SeatDetailView,
    SeatListCreateView,
    SeatRowDetailView,
    SeatRowListCreateView,
    SessionSeatDetailView,
    SessionSeatListCreateView,
    TicketDetailView,
    TicketListCreateView,
)
from users.models import User


REST_FRAMEWORK_OVERRIDE = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
    "EXCEPTION_HANDLER": "cinepolis_natal_api.exception_handler.standardized_exception_handler",
}


@pytest.fixture(autouse=True)
def disable_throttling_for_module():
    original_seat_row_list_throttles = SeatRowListCreateView.throttle_classes
    original_seat_row_detail_throttles = SeatRowDetailView.throttle_classes
    original_seat_list_throttles = SeatListCreateView.throttle_classes
    original_seat_detail_throttles = SeatDetailView.throttle_classes
    original_session_seat_list_throttles = SessionSeatListCreateView.throttle_classes
    original_session_seat_detail_throttles = SessionSeatDetailView.throttle_classes
    original_ticket_list_throttles = TicketListCreateView.throttle_classes
    original_ticket_detail_throttles = TicketDetailView.throttle_classes

    SeatRowListCreateView.throttle_classes = []
    SeatRowDetailView.throttle_classes = []
    SeatListCreateView.throttle_classes = []
    SeatDetailView.throttle_classes = []
    SessionSeatListCreateView.throttle_classes = []
    SessionSeatDetailView.throttle_classes = []
    TicketListCreateView.throttle_classes = []
    TicketDetailView.throttle_classes = []

    cache.clear()
    with override_settings(REST_FRAMEWORK=REST_FRAMEWORK_OVERRIDE):
        yield
    cache.clear()

    SeatRowListCreateView.throttle_classes = original_seat_row_list_throttles
    SeatRowDetailView.throttle_classes = original_seat_row_detail_throttles
    SeatListCreateView.throttle_classes = original_seat_list_throttles
    SeatDetailView.throttle_classes = original_seat_detail_throttles
    SessionSeatListCreateView.throttle_classes = original_session_seat_list_throttles
    SessionSeatDetailView.throttle_classes = original_session_seat_detail_throttles
    TicketListCreateView.throttle_classes = original_ticket_list_throttles
    TicketDetailView.throttle_classes = original_ticket_detail_throttles


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def room():
    return Room.objects.create(name="Room CRUD", capacity=50)


@pytest.fixture
def movie():
    return Movie.objects.create(
        title="Movie CRUD",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-29",
        poster_url="https://example.com/movie-crud.jpg",
    )


@pytest.fixture
def session(movie, room):
    now = timezone.now()
    return Session.objects.create(
        movie=movie,
        room=room,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=3),
    )


@pytest.mark.django_db
def test_seat_row_create_retrieve_delete_endpoints(api_client, room):
    create_response = api_client.post(
        "/api/v1/reservation/seat-rows/",
        {"room": str(room.id), "name": "a"},
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    seat_row_id = create_response.data["id"]
    assert create_response.data["name"] == "A"

    retrieve_response = api_client.get(
        f"/api/v1/reservation/seat-rows/{seat_row_id}/",
    )

    assert retrieve_response.status_code == status.HTTP_200_OK
    assert retrieve_response.data["name"] == "A"

    patch_response = api_client.patch(
        f"/api/v1/reservation/seat-rows/{seat_row_id}/",
        {"name": "b"},
        format="json",
    )

    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["name"] == "B"

    delete_response = api_client.delete(
        f"/api/v1/reservation/seat-rows/{seat_row_id}/"
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_seat_create_retrieve_delete_endpoints(api_client, room):
    seat_row = SeatRow.objects.create(room=room, name="A")

    create_response = api_client.post(
        "/api/v1/reservation/seats/",
        {"row": str(seat_row.id), "number": 1},
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    seat_id = create_response.data["id"]

    retrieve_response = api_client.get(
        f"/api/v1/reservation/seats/{seat_id}/",
    )

    assert retrieve_response.status_code == status.HTTP_200_OK
    assert retrieve_response.data["number"] == 1

    patch_response = api_client.patch(
        f"/api/v1/reservation/seats/{seat_id}/",
        {"number": 2},
        format="json",
    )

    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["number"] == 2

    delete_response = api_client.delete(f"/api/v1/reservation/seats/{seat_id}/")

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_session_seat_create_retrieve_delete_endpoints(api_client, room, session):
    seat_row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=seat_row, number=1)

    create_response = api_client.post(
        "/api/v1/reservation/session-seats/",
        {
            "session": str(session.id),
            "seat": str(seat.id),
            "status": SessionSeatStatus.AVAILABLE,
            "locked_by_user": None,
            "lock_expires_at": None,
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    session_seat_id = create_response.data["id"]

    retrieve_response = api_client.get(
        f"/api/v1/reservation/session-seats/{session_seat_id}/",
    )

    assert retrieve_response.status_code == status.HTTP_200_OK
    assert retrieve_response.data["status"] == SessionSeatStatus.AVAILABLE

    patch_response = api_client.patch(
        f"/api/v1/reservation/session-seats/{session_seat_id}/",
        {"status": SessionSeatStatus.PURCHASED},
        format="json",
    )

    assert patch_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    delete_response = api_client.delete(
        f"/api/v1/reservation/session-seats/{session_seat_id}/"
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_ticket_create_list_retrieve_delete_endpoints(api_client, room, session):
    user = User.objects.create_user(
        email="ticket-crud@example.com",
        username="ticketcrud",
        password="StrongPass123",
    )
    seat_row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=seat_row, number=1)

    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.PURCHASED,
    )

    create_response = api_client.post(
        "/api/v1/reservation/tickets/",
        {
            "user": str(user.id),
            "session_seat": str(session_seat.id),
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    ticket_id = create_response.data["id"]
    assert create_response.data["ticket_code"]

    retrieve_response = api_client.get(f"/api/v1/reservation/tickets/{ticket_id}/")

    assert retrieve_response.status_code == status.HTTP_200_OK
    assert retrieve_response.data["id"] == ticket_id

    list_response = api_client.get("/api/v1/reservation/tickets/")

    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1

    patch_response = api_client.patch(
        f"/api/v1/reservation/tickets/{ticket_id}/",
        {"user": str(user.id)},
        format="json",
    )

    assert patch_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    delete_response = api_client.delete(
        f"/api/v1/reservation/tickets/{ticket_id}/"
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
