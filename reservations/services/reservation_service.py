from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from catalog.models import Session
from reservations.exceptions import (
    InvalidSeatSelectionError,
    SeatUnavailableError,
    SessionNotFoundError,
)
from reservations.locks import SeatLockManager
from reservations.models import SessionSeat, SessionSeatStatus


class TemporaryReservationService:
    LOCK_DURATION_SECONDS = 600
    SEAT_UNAVAILABLE_MESSAGE = "One or more selected seats are not available."
    INVALID_SELECTION_MESSAGE = (
        "One or more selected seats do not belong to this session."
    )

    def __init__(self):
        self.lock_manager = SeatLockManager(
            timeout_seconds=self.LOCK_DURATION_SECONDS
        )

    def execute(self, *, session_id, seat_ids, user):
        session_exists = Session.objects.filter(id=session_id).exists()
        if not session_exists:
            raise SessionNotFoundError("Session not found.")

        ordered_seat_ids = sorted(seat_ids)

        session_seats = list(
            SessionSeat.objects.select_related("seat", "seat__row")
            .filter(session_id=session_id, seat_id__in=ordered_seat_ids)
            .order_by("seat_id")
        )

        if len(session_seats) != len(ordered_seat_ids):
            raise InvalidSeatSelectionError(self.INVALID_SELECTION_MESSAGE)

        for session_seat in session_seats:
            if session_seat.status != SessionSeatStatus.AVAILABLE:
                raise SeatUnavailableError(self.SEAT_UNAVAILABLE_MESSAGE)

        acquired_locks = []
        expires_at = timezone.now() + timedelta(
            seconds=self.LOCK_DURATION_SECONDS
        )

        try:
            for session_seat in session_seats:
                acquired = self.lock_manager.acquire(
                    session_id=session_id,
                    seat_id=session_seat.seat_id,
                    owner_id=user.id,
                )
                if not acquired:
                    raise SeatUnavailableError(self.SEAT_UNAVAILABLE_MESSAGE)

                acquired_locks.append(session_seat)

            with transaction.atomic():
                locked_session_seats = list(
                    SessionSeat.objects.select_for_update()
                    .select_related("seat", "seat__row")
                    .filter(
                        session_id=session_id,
                        seat_id__in=ordered_seat_ids,
                    )
                    .order_by("seat_id")
                )

                if len(locked_session_seats) != len(ordered_seat_ids):
                    raise InvalidSeatSelectionError(
                        self.INVALID_SELECTION_MESSAGE
                    )

                for session_seat in locked_session_seats:
                    if session_seat.status != SessionSeatStatus.AVAILABLE:
                        raise SeatUnavailableError(
                            self.SEAT_UNAVAILABLE_MESSAGE
                        )

                for session_seat in locked_session_seats:
                    session_seat.status = SessionSeatStatus.RESERVED
                    session_seat.locked_by_user = user
                    session_seat.lock_expires_at = expires_at

                SessionSeat.objects.bulk_update(
                    locked_session_seats,
                    ["status", "locked_by_user", "lock_expires_at"],
                )

            return {
                "session_id": session_id,
                "status": "TEMPORARILY_RESERVED",
                "expires_at": expires_at,
                "seats": locked_session_seats,
            }

        except Exception:
            for session_seat in acquired_locks:
                self.lock_manager.release(
                    session_id=session_id,
                    seat_id=session_seat.seat_id,
                )
            raise