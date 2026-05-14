from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Movie, Room, Session
from reservations.models import SessionSeat, SessionSeatStatus, Seat, SeatRow, Ticket
from reservations.services.checkout_service import CheckoutService, InvalidSeatStateError
from reservations.services.ticket_confirmation_email_service import (
    build_ticket_confirmation_email,
)


def _build_checkout_context(*, seat_numbers=(1, 2), reserved=True):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="email-checkout@example.com",
        username="email_checkout_user",
        password="StrongPass123!",
    )

    room = Room.objects.create(name="Email Checkout Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    movie = Movie.objects.create(
        title="Email Checkout Movie",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )

    start_time = timezone.now() + timedelta(hours=1)
    session = Session.objects.create(
        movie=movie,
        room=room,
        start_time=start_time,
        end_time=start_time + timedelta(hours=2),
    )

    seats = []
    session_seats = []
    for seat_number in seat_numbers:
        seat = Seat.objects.create(row=row, number=seat_number)
        seats.append(seat)

        session_seat = SessionSeat.objects.create(
            session=session,
            seat=seat,
            status=(
                SessionSeatStatus.RESERVED
                if reserved
                else SessionSeatStatus.AVAILABLE
            ),
            locked_by_user=user if reserved else None,
            lock_expires_at=(timezone.now() + timedelta(minutes=10)) if reserved else None,
        )
        session_seats.append(session_seat)

    return {
        "user": user,
        "session": session,
        "seats": seats,
        "session_seats": session_seats,
    }


@pytest.mark.django_db
def test_checkout_should_enqueue_ticket_confirmation_email_after_commit_only(
    django_capture_on_commit_callbacks,
):
    context = _build_checkout_context()
    service = CheckoutService()

    with patch.object(CheckoutService, "_release_redis_locks") as mocked_release_locks:
        with patch(
            "reservations.tasks.send_ticket_confirmation_email_task.apply_async"
        ) as mocked_apply_async:
            with django_capture_on_commit_callbacks(execute=False) as callbacks:
                service.execute(
                    session_id=context["session"].id,
                    seat_ids=[seat.id for seat in context["seats"]],
                    user=context["user"],
                )

            assert mocked_apply_async.call_count == 0
            assert len(callbacks) == 2

            for callback in callbacks:
                callback()

    mocked_release_locks.assert_called_once()
    mocked_apply_async.assert_called_once()

    created_ticket_ids = {
        str(ticket.id)
        for ticket in Ticket.objects.filter(user=context["user"])
    }

    task_call_kwargs = mocked_apply_async.call_args.kwargs
    assert task_call_kwargs["args"][0] == str(context["user"].id)
    assert set(task_call_kwargs["args"][1]) == created_ticket_ids


@pytest.mark.django_db
def test_checkout_should_not_schedule_email_task_when_checkout_fails():
    context = _build_checkout_context(seat_numbers=(1,), reserved=False)
    service = CheckoutService()

    with patch(
        "reservations.tasks.send_ticket_confirmation_email_task.apply_async"
    ) as mocked_apply_async:
        with pytest.raises(InvalidSeatStateError):
            service.execute(
                session_id=context["session"].id,
                seat_ids=[seat.id for seat in context["seats"]],
                user=context["user"],
            )

    mocked_apply_async.assert_not_called()
    assert Ticket.objects.filter(user=context["user"]).count() == 0


@pytest.mark.django_db
def test_ticket_confirmation_email_should_render_multiple_tickets_correctly():
    context = _build_checkout_context(seat_numbers=(1, 2), reserved=True)
    service = CheckoutService()

    with patch.object(CheckoutService, "_release_redis_locks"):
        service.execute(
            session_id=context["session"].id,
            seat_ids=[seat.id for seat in context["seats"]],
            user=context["user"],
        )

    tickets = list(
        Ticket.objects.select_related(
            "session_seat__session__movie",
            "session_seat__session__room",
            "session_seat__seat__row",
        )
        .filter(user=context["user"])
        .order_by("created_at")
    )

    email_payload = build_ticket_confirmation_email(
        user=context["user"],
        tickets=tickets,
    )

    assert email_payload["subject"] == "Ticket confirmation - 2 ticket(s)"
    assert "Email Checkout Movie" in email_payload["body"]
    assert "Room: Email Checkout Room" in email_payload["body"]
    assert "Seat: A1" in email_payload["body"]
    assert "Seat: A2" in email_payload["body"]

    for ticket in tickets:
        assert ticket.ticket_code in email_payload["body"]

    session_start_date = timezone.localtime(context["session"].start_time).strftime(
        "%Y-%m-%d"
    )
    assert session_start_date in email_payload["body"]
