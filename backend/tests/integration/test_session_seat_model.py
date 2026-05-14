import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalog.models import Movie, Room, Session
from reservations.models import Seat, SeatRow, SessionSeat, SessionSeatStatus
from users.models import User


@pytest.mark.django_db
def test_create_session_seat_with_default_available_status():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    session_seat = SessionSeat.objects.create(session=session, seat=seat)

    assert session_seat.status == SessionSeatStatus.AVAILABLE
    assert session_seat.locked_by_user is None
    assert session_seat.lock_expires_at is None


@pytest.mark.django_db
def test_session_seat_must_be_unique_per_session_and_seat():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    SessionSeat.objects.create(session=session, seat=seat)

    with pytest.raises(ValidationError):
        SessionSeat.objects.create(session=session, seat=seat)


@pytest.mark.django_db
def test_reserved_session_seat_requires_locked_user_and_expiration():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    with pytest.raises(ValidationError):
        SessionSeat.objects.create(
            session=session,
            seat=seat,
            status=SessionSeatStatus.RESERVED,
        )


@pytest.mark.django_db
def test_available_session_seat_cannot_have_lock_metadata():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)
    user = User.objects.create_user(
        email="user@example.com",
        username="user1",
        password="StrongPass123",
    )

    with pytest.raises(ValidationError):
        SessionSeat.objects.create(
            session=session,
            seat=seat,
            status=SessionSeatStatus.AVAILABLE,
            locked_by_user=user,
            lock_expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )


@pytest.mark.django_db
def test_purchased_session_seat_cannot_have_lock_expiration():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)
    user = User.objects.create_user(
        email="user@example.com",
        username="user1",
        password="StrongPass123",
    )

    with pytest.raises(ValidationError):
        SessionSeat.objects.create(
            session=session,
            seat=seat,
            status=SessionSeatStatus.PURCHASED,
            locked_by_user=user,
            lock_expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )


@pytest.mark.django_db
def test_session_seat_must_belong_to_same_room_as_session():
    room_1 = Room.objects.create(name="Room 1", capacity=100)
    room_2 = Room.objects.create(name="Room 2", capacity=100)

    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )

    session = Session.objects.create(
        movie=movie,
        room=room_1,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )

    row = SeatRow.objects.create(room=room_2, name="A")
    seat = Seat.objects.create(row=row, number=1)

    with pytest.raises(ValidationError):
        SessionSeat.objects.create(session=session, seat=seat)
     
   
@pytest.mark.django_db
def test_session_seat_string_representation():
    room = Room.objects.create(name="Room 1", capacity=100)
    movie = Movie.objects.create(
        title="Movie 1",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
    )
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)
    session_seat = SessionSeat.objects.create(session=session, seat=seat)

    assert str(session_seat) == "Movie 1 | Room 1 | A1 | AVAILABLE"