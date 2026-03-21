import pytest
from rest_framework.test import APIClient

from catalog.models import Movie, Room, Session
from reservations.models import Seat, SeatRow, SessionSeat, SessionSeatStatus
from users.models import User
from django.utils import timezone


@pytest.mark.django_db
def test_session_seat_map_returns_full_seat_map():
    client = APIClient()

    room = Room.objects.create(name="Room 1", capacity=100)
    row_a = SeatRow.objects.create(room=room, name="A")
    row_b = SeatRow.objects.create(room=room, name="B")

    seat_a1 = Seat.objects.create(row=row_a, number=1)
    seat_a2 = Seat.objects.create(row=row_a, number=2)
    seat_b1 = Seat.objects.create(row=row_b, number=1)

    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )

    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )

    SessionSeat.objects.bulk_create(
        [
            SessionSeat(session=session, seat=seat_a1, status=SessionSeatStatus.AVAILABLE),
            SessionSeat(session=session, seat=seat_a2, status=SessionSeatStatus.RESERVED, locked_by_user=User.objects.create_user(email="u1@example.com", username="u1", password="StrongPass123"), lock_expires_at=timezone.now() + timezone.timedelta(minutes=10)),
            SessionSeat(session=session, seat=seat_b1, status=SessionSeatStatus.PURCHASED),
        ]
    )

    response = client.get(f"/api/v1/catalog/sessions/{session.id}/seats/")

    assert response.status_code == 200
    assert response.data == [
        {
            "seat_id": str(seat_a1.id),
            "row": "A",
            "number": 1,
            "status": "AVAILABLE",
        },
        {
            "seat_id": str(seat_a2.id),
            "row": "A",
            "number": 2,
            "status": "RESERVED",
        },
        {
            "seat_id": str(seat_b1.id),
            "row": "B",
            "number": 1,
            "status": "PURCHASED",
        },
    ]


@pytest.mark.django_db
def test_session_seat_map_is_publicly_accessible():
    client = APIClient()

    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )

    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )

    SessionSeat.objects.create(session=session, seat=seat)

    response = client.get(f"/api/v1/catalog/sessions/{session.id}/seats/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_session_seat_map_returns_404_for_unknown_session():
    client = APIClient()

    response = client.get("/api/v1/catalog/sessions/00000000-0000-0000-0000-000000000000/seats/")

    assert response.status_code == 404