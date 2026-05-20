from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Movie, Room, Session
from reservations.models import Seat, SeatRow, SessionSeat, SessionSeatStatus, Ticket
from users.models import User


@pytest.fixture
def admin_client():
    admin = User.objects.create_user(
        email="domain-admin@example.com",
        username="domain_admin",
        password="StrongPass123",
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.fixture
def movie():
    return Movie.objects.create(
        title=f"Domain Movie {Movie.objects.count() + 1}",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )


def create_future_session(movie, room, *, base_price="30.00"):
    start_time = timezone.now() + timedelta(days=1)
    return Session.objects.create(
        movie=movie,
        room=room,
        start_time=start_time,
        end_time=start_time + timedelta(hours=2),
        base_price=base_price,
    )


@pytest.mark.django_db
def test_room_capacity_cannot_be_lower_than_registered_seats(admin_client):
    room = Room.objects.create(name="Capacity Room", capacity=2)
    row = SeatRow.objects.create(room=room, name="A")
    Seat.objects.create(row=row, number=1)
    Seat.objects.create(row=row, number=2)

    response = admin_client.patch(
        f"/api/v1/catalog/rooms/{room.id}/",
        {"capacity": 1},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "capacity" in response.data["error"]["details"]
    room.refresh_from_db()
    assert room.capacity == 2


@pytest.mark.django_db
def test_room_capacity_cannot_be_exceeded_by_new_seats(admin_client):
    room = Room.objects.create(name="Full Room", capacity=1)
    row = SeatRow.objects.create(room=room, name="A")
    Seat.objects.create(row=row, number=1)

    response = admin_client.post(
        "/api/v1/reservation/seats/",
        {"row": str(row.id), "number": 2},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "row" in response.data["error"]["details"]
    assert Seat.objects.filter(row=row).count() == 1


@pytest.mark.django_db
def test_session_creation_generates_seat_map_and_blocks_future_layout_changes(
    admin_client,
    movie,
):
    room = Room.objects.create(name="Session Layout Room", capacity=2)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    response = admin_client.post(
        "/api/v1/catalog/sessions/",
        {
            "movie": str(movie.id),
            "room": str(room.id),
            "start_time": (timezone.now() + timedelta(days=1)).isoformat(),
            "end_time": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
            "base_price": "30.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    session = Session.objects.get(id=response.data["id"])
    assert list(
        SessionSeat.objects.filter(session=session).values_list("seat_id", flat=True)
    ) == [seat.id]

    create_seat_response = admin_client.post(
        "/api/v1/reservation/seats/",
        {"row": str(row.id), "number": 2},
        format="json",
    )
    delete_seat_response = admin_client.delete(f"/api/v1/reservation/seats/{seat.id}/")

    assert create_seat_response.status_code == status.HTTP_400_BAD_REQUEST
    assert delete_seat_response.status_code == status.HTTP_400_BAD_REQUEST
    assert SessionSeat.objects.filter(session=session).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "value_factory"),
    [
        ("movie", lambda context: str(context["other_movie"].id)),
        ("room", lambda context: str(context["other_room"].id)),
        (
            "start_time",
            lambda context: (timezone.now() + timedelta(days=2)).isoformat(),
        ),
        (
            "end_time",
            lambda context: (timezone.now() + timedelta(days=2, hours=2)).isoformat(),
        ),
        ("base_price", lambda context: "45.00"),
    ],
)
def test_reserved_session_sensitive_fields_cannot_be_mutated(
    admin_client,
    movie,
    field,
    value_factory,
):
    room = Room.objects.create(name="Reserved Session Room", capacity=1)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)
    session = create_future_session(movie, room)
    SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.RESERVED,
        locked_by_user=User.objects.create_user(
            email="reserved-user@example.com",
            username="reserved_user",
            password="StrongPass123",
        ),
        lock_expires_at=timezone.now() + timedelta(minutes=10),
    )
    other_room = Room.objects.create(name="Other Session Room", capacity=1)
    other_movie = Movie.objects.create(
        title="Other Domain Movie",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-22",
        poster_url="https://example.com/other-poster.jpg",
    )
    context = {"other_room": other_room, "other_movie": other_movie}

    response = admin_client.patch(
        f"/api/v1/catalog/sessions/{session.id}/",
        {field: value_factory(context)},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    session.refresh_from_db()
    assert session.movie_id == movie.id
    assert session.room_id == room.id
    assert session.base_price == Decimal("30.00")


@pytest.mark.django_db
def test_purchased_ticket_history_is_protected_from_session_price_changes(
    admin_client,
    movie,
):
    user = User.objects.create_user(
        email="ticket-owner@example.com",
        username="ticket_owner",
        password="StrongPass123",
    )
    room = Room.objects.create(name="Purchased Session Room", capacity=1)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)
    session = create_future_session(movie, room)
    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.PURCHASED,
    )
    ticket = Ticket.objects.create(
        user=user,
        session_seat=session_seat,
        ticket_type="inteira",
        amount_paid="30.00",
        payment_method="pix",
    )

    response = admin_client.patch(
        f"/api/v1/catalog/sessions/{session.id}/",
        {"base_price": "45.00"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    session.refresh_from_db()
    ticket.refresh_from_db()
    assert session.base_price == Decimal("30.00")
    assert ticket.amount_paid == Decimal("30.00")
