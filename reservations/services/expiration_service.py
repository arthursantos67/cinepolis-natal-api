from django.db import transaction
from django.utils import timezone

from reservations.locks import SeatLockManager
from reservations.models import SessionSeat, SessionSeatStatus


class ExpiredSeatReleaseService:
    def __init__(self):
        self.lock_manager = SeatLockManager()

    def execute(self, *, session_seat_id) -> bool:
        now = timezone.now()

        with transaction.atomic():
            session_seat = (
                SessionSeat.objects.select_for_update()
                .filter(id=session_seat_id)
                .first()
            )

            if session_seat is None:
                return False

            if session_seat.status != SessionSeatStatus.RESERVED:
                return False

            if session_seat.lock_expires_at is None:
                return False

            if session_seat.lock_expires_at > now:
                return False

            session_id = session_seat.session_id
            seat_id = session_seat.seat_id

            session_seat.status = SessionSeatStatus.AVAILABLE
            session_seat.locked_by_user = None
            session_seat.lock_expires_at = None
            session_seat.save(
                update_fields=["status", "locked_by_user", "lock_expires_at"]
            )

        self.lock_manager.release(
            session_id=session_id,
            seat_id=seat_id,
        )
        return True