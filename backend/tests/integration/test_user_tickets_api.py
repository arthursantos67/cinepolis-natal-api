import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import Movie, Room, Session
from reservations.models import Ticket, SessionSeat, SessionSeatStatus, Seat, SeatRow


@pytest.mark.django_db
def test_should_return_only_authenticated_user_tickets():
    user_model = get_user_model()

    user1 = user_model.objects.create_user(
        email="user1@test.com",
        username="user1",
        password="123456",
    )

    user2 = user_model.objects.create_user(
        email="user2@test.com",
        username="user2",
        password="123456",
    )

    client = APIClient()
    client.force_authenticate(user=user1)

    room = Room.objects.create(name="Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Movie",
        synopsis="...",
        duration_minutes=120,
        release_date="2026-01-01",
        poster_url="http://test.com",
    )

    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now() + timedelta(hours=1),
        end_time=timezone.now() + timedelta(hours=2),
    )

    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.PURCHASED,
    )

    Ticket.objects.create(user=user1, session_seat=session_seat)

    # Ticket de outro usuário (não deve aparecer)
    session_seat_2 = SessionSeat.objects.create(
        session=session,
        seat=Seat.objects.create(row=row, number=2),
        status=SessionSeatStatus.PURCHASED,
    )
    Ticket.objects.create(user=user2, session_seat=session_seat_2)

    response = client.get("/api/v1/users/me/tickets/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    
@pytest.mark.django_db
def test_should_return_only_upcoming_tickets():
    user = get_user_model().objects.create_user(
        email="user@test.com",
        username="user",
        password="123456",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    room = Room.objects.create(name="Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    movie = Movie.objects.create(
        title="Movie",
        synopsis="...",
        duration_minutes=120,
        release_date="2026-01-01",
        poster_url="http://test.com",
    )

    # FUTURE session
    future_session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=2),
    )

    seat1 = Seat.objects.create(row=row, number=1)
    ss1 = SessionSeat.objects.create(
        session=future_session,
        seat=seat1,
        status=SessionSeatStatus.PURCHASED,
    )
    Ticket.objects.create(user=user, session_seat=ss1)

    # PAST session
    past_session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now() - timedelta(days=1),
        end_time=timezone.now() - timedelta(hours=1),
    )

    seat2 = Seat.objects.create(row=row, number=2)
    ss2 = SessionSeat.objects.create(
        session=past_session,
        seat=seat2,
        status=SessionSeatStatus.PURCHASED,
    )
    Ticket.objects.create(user=user, session_seat=ss2)

    response = client.get("/api/v1/users/me/tickets/?type=upcoming")

    assert response.status_code == 200
    assert response.data["count"] == 1
    
@pytest.mark.django_db
def test_should_return_only_past_tickets():
    user = get_user_model().objects.create_user(
        email="user@test.com",
        username="user",
        password="123456",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    room = Room.objects.create(name="Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    movie = Movie.objects.create(
        title="Movie",
        synopsis="...",
        duration_minutes=120,
        release_date="2026-01-01",
        poster_url="http://test.com",
    )

    past_session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now() - timedelta(days=1),
        end_time=timezone.now() - timedelta(hours=1),
    )

    seat = Seat.objects.create(row=row, number=1)
    ss = SessionSeat.objects.create(
        session=past_session,
        seat=seat,
        status=SessionSeatStatus.PURCHASED,
    )
    Ticket.objects.create(user=user, session_seat=ss)

    response = client.get("/api/v1/users/me/tickets/?type=past")

    assert response.status_code == 200
    assert response.data["count"] == 1
    
@pytest.mark.django_db
def test_should_require_authentication():
    client = APIClient()

    response = client.get("/api/v1/users/me/tickets/")

    assert response.status_code == 401