from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from catalog.models import Movie, Room, Session
from reservations.models import SessionSeat, SessionSeatStatus, Seat, SeatRow


@pytest.mark.django_db
def test_checkout_should_purchase_reserved_seats_successfully():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="checkout@example.com",
        username="checkout_user",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    room = Room.objects.create(name="Checkout Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Checkout Movie",
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
        status=SessionSeatStatus.RESERVED,
        locked_by_user=user,
        lock_expires_at=timezone.now() + timedelta(minutes=10),
    )

    response = client.post(
        "/api/v1/reservation/checkout/",
        {
            "session_id": str(session.id),
            "seat_ids": [str(seat.id)],
        },
        format="json",
    )

    assert response.status_code == 200

    session_seat.refresh_from_db()
    assert session_seat.status == SessionSeatStatus.PURCHASED
    assert session_seat.locked_by_user is None
    assert session_seat.lock_expires_at is None

    assert response.data["status"] == "PURCHASED"
    assert response.data["session_id"] == str(session.id)
    assert len(response.data["seats"]) == 1
    assert response.data["seats"][0]["seat_id"] == str(seat.id)
    assert response.data["seats"][0]["status"] == "PURCHASED"
    
@pytest.mark.django_db
def test_checkout_should_fail_for_expired_reservation():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="expired@example.com",
        username="expired_checkout_user",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    room = Room.objects.create(name="Expired Checkout Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Expired Checkout Movie",
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
        status=SessionSeatStatus.RESERVED,
        locked_by_user=user,
        lock_expires_at=timezone.now() - timedelta(minutes=1),
    )

    response = client.post(
        "/api/v1/reservation/checkout/",
        {
            "session_id": str(session.id),
            "seat_ids": [str(seat.id)],
        },
        format="json",
    )

    assert response.status_code == 409
    assert response.data["error"]["code"] == "SEAT_ALREADY_RESERVED"
    assert response.data["error"]["status"] == 409

    session_seat.refresh_from_db()
    assert session_seat.status == SessionSeatStatus.RESERVED
    assert session_seat.locked_by_user == user
    assert session_seat.lock_expires_at is not None
    
@pytest.mark.django_db
def test_checkout_should_fail_for_different_user():
    user_model = get_user_model()

    owner = user_model.objects.create_user(
        email="owner@example.com",
        username="owner_user",
        password="StrongPass123!",
    )

    another_user = user_model.objects.create_user(
        email="other@example.com",
        username="other_user",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=another_user)

    room = Room.objects.create(name="Ownership Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    movie = Movie.objects.create(
        title="Ownership Movie",
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
        status=SessionSeatStatus.RESERVED,
        locked_by_user=owner,
        lock_expires_at=timezone.now() + timedelta(minutes=10),
    )

    response = client.post(
        "/api/v1/reservation/checkout/",
        {
            "session_id": str(session.id),
            "seat_ids": [str(seat.id)],
        },
        format="json",
    )

    assert response.status_code == 403
    assert response.data["error"]["code"] == "PERMISSION_DENIED"
    assert response.data["error"]["status"] == 403

    session_seat.refresh_from_db()
    assert session_seat.status == SessionSeatStatus.RESERVED
    
@pytest.mark.django_db
def test_checkout_should_be_atomic_when_one_seat_is_invalid():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="atomic@example.com",
        username="atomic_user",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    room = Room.objects.create(name="Atomic Room", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    seat_valid = Seat.objects.create(row=row, number=1)
    seat_invalid = Seat.objects.create(row=row, number=2)

    movie = Movie.objects.create(
        title="Atomic Movie",
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

    session_seat_valid = SessionSeat.objects.create(
        session=session,
        seat=seat_valid,
        status=SessionSeatStatus.RESERVED,
        locked_by_user=user,
        lock_expires_at=timezone.now() + timedelta(minutes=10),
    )

    session_seat_invalid = SessionSeat.objects.create(
        session=session,
        seat=seat_invalid,
        status=SessionSeatStatus.AVAILABLE,  # <- inválido
    )

    response = client.post(
        "/api/v1/reservation/checkout/",
        {
            "session_id": str(session.id),
            "seat_ids": [str(seat_valid.id), str(seat_invalid.id)],
        },
        format="json",
    )

    assert response.status_code == 409

    session_seat_valid.refresh_from_db()
    session_seat_invalid.refresh_from_db()

    assert session_seat_valid.status == SessionSeatStatus.RESERVED
    assert session_seat_invalid.status == SessionSeatStatus.AVAILABLE
    
@pytest.mark.django_db
def test_list_movies_should_use_cache_on_second_request():
    cache.clear()

    Movie.objects.create(
        title="Cached Checkout Movie",
        synopsis="Synopsis",
        duration_minutes=120,
        release_date="2026-03-21",
        poster_url="https://example.com/poster.jpg",
    )

    api_client = APIClient()

    with CaptureQueriesContext(connection) as first_request_queries:
        first_response = api_client.get("/api/v1/catalog/movies/")

    with CaptureQueriesContext(connection) as second_request_queries:
        second_response = api_client.get("/api/v1/catalog/movies/")

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert first_response.data == second_response.data
    assert len(second_request_queries) < len(first_request_queries)
    cache.clear()