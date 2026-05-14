import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Movie, Room, Session
from reservations.models import (
    SessionSeat,
    SessionSeatStatus,
    Seat,
    SeatRow,
    Ticket,
)


@pytest.mark.django_db
def test_should_create_ticket_for_purchased_seat():
    user = get_user_model().objects.create_user(
        email="user@test.com",
        username="user_ticket",
        password="123456",
    )

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
        start_time=timezone.now(),
        end_time=timezone.now(),
    )

    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.PURCHASED,
    )

    ticket = Ticket.objects.create(
        user=user,
        session_seat=session_seat,
    )

    assert ticket.id is not None
    assert ticket.ticket_code is not None
    assert ticket.session_seat == session_seat


@pytest.mark.django_db
def test_should_not_allow_ticket_for_non_purchased_seat():
    user = get_user_model().objects.create_user(
        email="user@test.com",
        username="user_ticket_invalid",
        password="123456",
    )

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
        start_time=timezone.now(),
        end_time=timezone.now(),
    )

    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.AVAILABLE,
    )

    with pytest.raises(Exception):
        Ticket.objects.create(
            user=user,
            session_seat=session_seat,
        )


@pytest.mark.django_db
def test_should_generate_unique_ticket_codes():
    user = get_user_model().objects.create_user(
        email="user@test.com",
        username="user_ticket_unique",
        password="123456",
    )

    room = Room.objects.create(name="Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

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
        start_time=timezone.now(),
        end_time=timezone.now(),
    )

    seat1 = Seat.objects.create(row=row, number=1)
    seat2 = Seat.objects.create(row=row, number=2)

    ss1 = SessionSeat.objects.create(
        session=session,
        seat=seat1,
        status=SessionSeatStatus.PURCHASED,
    )

    ss2 = SessionSeat.objects.create(
        session=session,
        seat=seat2,
        status=SessionSeatStatus.PURCHASED,
    )

    ticket1 = Ticket.objects.create(user=user, session_seat=ss1)
    ticket2 = Ticket.objects.create(user=user, session_seat=ss2)

    assert ticket1.ticket_code != ticket2.ticket_code