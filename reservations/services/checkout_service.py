from django.db import transaction
from django.utils import timezone

from cinepolis_natal_api.logging_context import get_correlation_id
from reservations.locks import SeatLockManager
from reservations.models import SessionSeat, SessionSeatStatus, Ticket


class CheckoutError(Exception):
    pass


class InvalidSeatSelectionError(CheckoutError):
    pass


class ReservationOwnershipError(CheckoutError):
    pass


class ExpiredReservationError(CheckoutError):
    pass


class InvalidSeatStateError(CheckoutError):
    pass


class CheckoutService:
    INVALID_SELECTION_MESSAGE = (
        "One or more selected seats do not belong to this session."
    )
    OWNERSHIP_MESSAGE = "One or more selected seats are not locked by this user."
    EXPIRED_MESSAGE = "One or more selected seats have expired reservations."
    INVALID_STATE_MESSAGE = "One or more selected seats are not available for checkout."

    def __init__(self):
        self.lock_manager = SeatLockManager()

    @transaction.atomic
    def execute(self, *, session_id, seat_ids, user):
        ordered_seat_ids = sorted(set(seat_ids))
        now = timezone.now()

        session_seats = list(
            SessionSeat.objects.select_for_update()
            .select_related("seat", "seat__row")
            .filter(
                session_id=session_id,
                seat_id__in=ordered_seat_ids,
            )
            .order_by("seat_id")
        )

        if len(session_seats) != len(ordered_seat_ids):
            raise InvalidSeatSelectionError(self.INVALID_SELECTION_MESSAGE)

        purchased_seats = []

        for session_seat in session_seats:
            if session_seat.status != SessionSeatStatus.RESERVED:
                raise InvalidSeatStateError(self.INVALID_STATE_MESSAGE)

            if session_seat.locked_by_user_id != user.id:
                raise ReservationOwnershipError(self.OWNERSHIP_MESSAGE)

            if (
                session_seat.lock_expires_at is None
                or session_seat.lock_expires_at <= now
            ):
                raise ExpiredReservationError(self.EXPIRED_MESSAGE)

            session_seat.status = SessionSeatStatus.PURCHASED
            session_seat.locked_by_user = None
            session_seat.lock_expires_at = None
            purchased_seats.append(session_seat)

        SessionSeat.objects.bulk_update(
            purchased_seats,
            ["status", "locked_by_user", "lock_expires_at"],
        )

        tickets = []
        for session_seat in purchased_seats:
            ticket = Ticket.objects.create(
                user=user,
                session_seat=session_seat,
            )
            tickets.append(ticket)

        ticket_ids = [str(ticket.id) for ticket in tickets]
        correlation_id = get_correlation_id()

        transaction.on_commit(
            lambda: self._release_redis_locks(
                session_id=session_id,
                session_seats=purchased_seats,
            )
        )

        transaction.on_commit(
            lambda: self._enqueue_ticket_confirmation_email(
                user_id=str(user.id),
                ticket_ids=ticket_ids,
                correlation_id=correlation_id,
            )
        )

        return {
            "status": "PURCHASED",
            "session_id": session_id,
            "seats": [
                {
                    "seat_id": str(session_seat.seat_id),
                    "row": session_seat.seat.row.name,
                    "number": session_seat.seat.number,
                    "status": session_seat.status,
                }
                for session_seat in purchased_seats
            ],
            "tickets": [
                {
                    "ticket_id": str(ticket.id),
                    "ticket_code": ticket.ticket_code,
                    "seat_id": str(ticket.session_seat.seat_id),
                }
                for ticket in tickets
            ],
        }

    def _release_redis_locks(self, *, session_id, session_seats):
        for session_seat in session_seats:
            self.lock_manager.release(
                session_id=session_id,
                seat_id=session_seat.seat_id,
            )

    @staticmethod
    def _enqueue_ticket_confirmation_email(*, user_id, ticket_ids, correlation_id):
        from reservations.tasks import send_ticket_confirmation_email_task

        apply_async_kwargs = {
            "args": [user_id, ticket_ids],
        }

        if correlation_id:
            apply_async_kwargs["headers"] = {
                "correlation_id": correlation_id,
            }

        send_ticket_confirmation_email_task.apply_async(**apply_async_kwargs)