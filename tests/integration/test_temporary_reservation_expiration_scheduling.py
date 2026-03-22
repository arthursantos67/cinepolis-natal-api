from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Movie, Room, Session
from reservations.models import SessionSeat, SessionSeatStatus, Seat, SeatRow
from reservations.services.reservation_service import TemporaryReservationService


@pytest.mark.django_db
def test_should_schedule_expiration_task_after_temporary_reservation(
    django_capture_on_commit_callbacks,
):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="user@example.com",
        username="user_schedule_expiration",
        password="StrongPass123!",
    )

    room = Room.objects.create(name="Room Scheduling", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Movie Scheduling",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )

    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=timezone.now() + timedelta(hours=1),
        end_time=timezone.now() + timedelta(hours=3),
    )

    session_seat = SessionSeat.objects.create(
        session=session,
        seat=seat,
        status=SessionSeatStatus.AVAILABLE,
    )

    service = TemporaryReservationService()

    with patch(
        "reservations.tasks.release_expired_session_seat.apply_async"
    ) as mocked_apply_async:
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            result = service.execute(
                session_id=session.id,
                seat_ids=[seat.id],
                user=user,
            )

    assert result["status"] == "TEMPORARILY_RESERVED"
    assert result["session_id"] == session.id

    session_seat.refresh_from_db()
    assert session_seat.status == SessionSeatStatus.RESERVED
    assert session_seat.locked_by_user == user
    assert session_seat.lock_expires_at is not None

    assert len(callbacks) == 1

    mocked_apply_async.assert_called_once()

    call_kwargs = mocked_apply_async.call_args.kwargs
    assert call_kwargs["args"] == [str(session_seat.id)]
    assert call_kwargs["eta"] == session_seat.lock_expires_at