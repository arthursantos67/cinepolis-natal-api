from celery import shared_task

from reservations.services import ExpiredSeatReleaseService


@shared_task
def release_expired_session_seat(session_seat_id: str) -> None:
    service = ExpiredSeatReleaseService()
    service.execute(session_seat_id=session_seat_id)