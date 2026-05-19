from django.db import transaction
from django.utils import timezone

from reservations.locks import SeatLockManager
from reservations.models import SessionSeat, SessionSeatStatus


class TemporaryReservationReleaseError(Exception):
    pass


class InvalidSessionSeatSelectionError(TemporaryReservationReleaseError):
    pass


class ReleaseReservationOwnershipError(TemporaryReservationReleaseError):
    pass


class ExpiredReservationReleaseError(TemporaryReservationReleaseError):
    pass


class InvalidReservationReleaseStateError(TemporaryReservationReleaseError):
    pass


class TemporaryReservationReleaseService:
    INVALID_SELECTION_MESSAGE = (
        "One or more selected session seats do not belong to this session."
    )
    OWNERSHIP_MESSAGE = "One or more selected seats are not locked by this user."
    EXPIRED_MESSAGE = "One or more selected seats have expired reservations."
    INVALID_STATE_MESSAGE = "One or more selected seats are not reserved."

    def __init__(self):
        self.lock_manager = SeatLockManager()

    def execute(self, *, session_id, session_seat_ids, user):
        ordered_session_seat_ids = sorted(set(session_seat_ids))
        now = timezone.now()

        with transaction.atomic():
            session_seats = list(
                SessionSeat.objects.select_for_update()
                .select_related("seat", "seat__row")
                .filter(
                    session_id=session_id,
                    id__in=ordered_session_seat_ids,
                )
                .order_by("id")
            )

            if len(session_seats) != len(ordered_session_seat_ids):
                raise InvalidSessionSeatSelectionError(self.INVALID_SELECTION_MESSAGE)

            for session_seat in session_seats:
                if session_seat.status != SessionSeatStatus.RESERVED:
                    raise InvalidReservationReleaseStateError(
                        self.INVALID_STATE_MESSAGE
                    )

                if session_seat.locked_by_user_id != user.id:
                    raise ReleaseReservationOwnershipError(self.OWNERSHIP_MESSAGE)

                if (
                    session_seat.lock_expires_at is None
                    or session_seat.lock_expires_at <= now
                ):
                    raise ExpiredReservationReleaseError(self.EXPIRED_MESSAGE)

            for session_seat in session_seats:
                session_seat.status = SessionSeatStatus.AVAILABLE
                session_seat.locked_by_user = None
                session_seat.lock_expires_at = None

            SessionSeat.objects.bulk_update(
                session_seats,
                ["status", "locked_by_user", "lock_expires_at"],
            )

        self._release_redis_locks(
            session_id=session_id,
            session_seats=session_seats,
        )

        return {
            "session_id": session_id,
            "status": "RELEASED",
            "seats": session_seats,
        }

    def _release_redis_locks(self, *, session_id, session_seats):
        for session_seat in session_seats:
            self.lock_manager.release(
                session_id=session_id,
                seat_id=session_seat.seat_id,
            )
