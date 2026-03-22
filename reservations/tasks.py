import hashlib
import logging
import smtplib

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail

from reservations.models import Ticket
from reservations.services import ExpiredSeatReleaseService
from reservations.services.ticket_confirmation_email_service import (
    build_ticket_confirmation_email,
)


logger = logging.getLogger(__name__)


@shared_task
def release_expired_session_seat(session_seat_id: str) -> None:
    service = ExpiredSeatReleaseService()
    service.execute(session_seat_id=session_seat_id)


@shared_task(
    bind=True,
    autoretry_for=(smtplib.SMTPException, ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_ticket_confirmation_email_task(self, user_id: str, ticket_ids: list[str]) -> None:
    normalized_ticket_ids = sorted({str(ticket_id) for ticket_id in ticket_ids})
    if not normalized_ticket_ids:
        logger.warning(
            "Ticket confirmation email skipped because no tickets were provided | user_id=%s",
            user_id,
        )
        return

    cache_fingerprint = hashlib.sha256(
        f"{user_id}:{','.join(normalized_ticket_ids)}".encode()
    ).hexdigest()
    sent_cache_key = f"ticket_confirmation_email:sent:{cache_fingerprint}"

    if cache.get(sent_cache_key):
        logger.info(
            "Ticket confirmation email skipped because it was already sent | user_id=%s ticket_ids=%s",
            user_id,
            normalized_ticket_ids,
        )
        return

    user_model = get_user_model()
    user = user_model.objects.filter(id=user_id).first()
    if user is None:
        logger.warning(
            "Ticket confirmation email skipped because user was not found | user_id=%s",
            user_id,
        )
        return

    tickets = list(
        Ticket.objects.select_related(
            "session_seat__session__movie",
            "session_seat__session__room",
            "session_seat__seat__row",
        )
        .filter(id__in=normalized_ticket_ids, user_id=user_id)
        .order_by("created_at")
    )

    if not tickets:
        logger.warning(
            "Ticket confirmation email skipped because no ticket records were found | user_id=%s ticket_ids=%s",
            user_id,
            normalized_ticket_ids,
        )
        return

    email_payload = build_ticket_confirmation_email(user=user, tickets=tickets)
    try:
        send_mail(
            subject=email_payload["subject"],
            message=email_payload["body"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError, OSError):
        logger.exception(
            "Ticket confirmation email delivery failed",
            extra={
                "task_id": getattr(self.request, "id", None),
                "task_name": self.name,
                "user_id": user_id,
                "ticket_ids": normalized_ticket_ids,
            },
        )
        raise

    cache.set(
        sent_cache_key,
        "1",
        timeout=settings.TICKET_CONFIRMATION_EMAIL_SENT_TTL_SECONDS,
    )

    logger.info(
        "Ticket confirmation email sent | user_id=%s ticket_count=%s ticket_ids=%s",
        user_id,
        len(tickets),
        normalized_ticket_ids,
    )