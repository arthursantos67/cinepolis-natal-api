# Cinepolis Natal API

Production-oriented REST API for a movie ticket reservation system. The platform allows users to register, authenticate with JWT, browse movie sessions, inspect real-time seat availability, reserve seats temporarily with distributed locking, complete checkout, and access personal tickets.

## Project Overview

This project represents the backend for a cinema reservation workflow where ticket purchase must remain consistent under concurrent access.

Business context:
- Public users browse catalog data (movies, sessions, rooms, genres, seat map).
- Authenticated users reserve seats temporarily and complete checkout.
- The system protects seat integrity with Redis locking, database constraints, and transactional flows.
- Ticket confirmation is processed asynchronously by Celery.

These capabilities are implemented with emphasis on data consistency, concurrency safety, and production-readiness.

## Documentation

Detailed implementation-aligned requirements are available in [`cinepolis-natal-api-srs.md`](./cinepolis-natal-api-srs.md).

## Tech Stack

- Python 3.14
- Django 6 + Django REST Framework
- JWT auth via `djangorestframework-simplejwt`
- PostgreSQL 17
- Redis 7 (`django-redis` cache + distributed locks)
- Celery (Redis broker)
- OpenAPI/Swagger via `drf-spectacular`
- Docker + Docker Compose
- GitHub Actions CI
- Pytest + pytest-django

## Features and Requirements Mapping

The table below maps implemented requirements to concrete endpoints/components.

| Requirement | Implemented behavior | Where in implementation |
| --- | --- | --- |
| User registration | Register with email, username, password | `POST /api/v1/auth/register/` (`users.views.UserRegistrationView`) |
| JWT login | Login returns access + refresh tokens | `POST /api/v1/auth/login/` (`users.views.UserLoginView`) |
| Current user profile | Returns authenticated user identity | `GET /api/v1/auth/me/` and `GET /api/v1/users/me/` |
| Public catalog | List/create/retrieve/delete genres, movies, rooms, sessions (no update endpoint implemented) | `catalog.views.*` under `/api/v1/catalog/*` |
| Session seat map | Public seat status (`AVAILABLE`, `RESERVED`, `PURCHASED`) | `GET /api/v1/reservation/sessions/{session_id}/seats/` |
| Temporary reservation | Authenticated seat lock with expiration metadata | `POST /api/v1/reservation/sessions/{session_id}/reservations/` |
| Checkout | Transactional purchase and ticket creation | `POST /api/v1/reservation/checkout/` + `reservations.services.checkout_service` |
| My tickets | Authenticated ticket list + `type=upcoming|past` filter | `GET /api/v1/users/me/tickets/` |
| Standardized errors | Unified error envelope for 4xx/5xx | `cinepolis_natal_api.exception_handler.standardized_exception_handler` |
| Rate limiting | Global + login + reservation throttles | `cinepolis_natal_api.throttling` + DRF settings |
| Redis cache | Caching for movies/sessions list endpoints + invalidation | `catalog.views.MovieListCreateView` / `SessionListCreateView` |
| Async jobs | Expiration release + ticket email notification | `reservations.tasks` + Celery worker |
| Health check | DB/Redis/Celery health status | `GET /health/` |
| API docs | OpenAPI schema + Swagger UI | `/api/schema/`, `/api/docs/` |

### Use Cases (1–7)

1. **User Registration**: create account with unique email and username.
2. **User Login**: authenticate and receive JWT tokens.
3. **Browse Movies**: list available movies and metadata.
4. **Browse Sessions**: list available sessions with movie + room data.
5. **View Seat Map**: inspect seat availability by session.
6. **Reserve + Checkout**: temporarily reserve seats, then finalize purchase.
7. **View My Tickets**: retrieve authenticated user ticket history (upcoming/past).

## Architecture Overview

### High-level design

- **Presentation layer**: DRF views/serializers expose HTTP API.
- **Domain/data layer**: Django models with relational and integrity constraints.
- **Service layer**: reservation/checkout/expiration services encapsulate transactional business logic.
- **Infrastructure**:
	- PostgreSQL as source of truth
	- Redis for cache and lock keys
	- Celery worker for asynchronous operations

### Architectural decisions

- **Modular monolith**: chosen to keep domain boundaries explicit while preserving deployment simplicity and transactional consistency.
- **Redis**: used for two latency/consistency-critical concerns, catalog caching and distributed seat locks.
- **Celery**: used to offload non-request-bound work (reservation expiration and ticket confirmation email).
- **Centralized error handler**: used to enforce a stable API contract and consistent observability across all endpoints.

### Redis locking strategy

- Lock key format: `lock:session-seat:{session_id}:{seat_id}`.
- Lock acquisition uses `cache.add` (atomic set-if-not-exists semantics).
- Temporary reservation duration: 600 seconds.
- Locks are released on checkout completion or expiration task execution.

### Celery async flows

- `release_expired_session_seat(session_seat_id)`:
	- runs at reservation expiration time
	- turns expired reserved seats back to `AVAILABLE`
	- releases Redis lock
- `send_ticket_confirmation_email_task(user_id, ticket_ids)`:
	- executed after successful checkout
	- has retry strategy for transient SMTP/network failures
	- includes idempotency guard via Redis cache fingerprint

### Error handling approach

- A centralized DRF exception handler returns a consistent `error` envelope.
- Handles validation/auth/permission/not-found/conflict/throttle/internal errors consistently.
- Internal exceptions are logged with contextual metadata while returning sanitized 500 responses.

### Scalability considerations already implemented

- Stateless JWT authentication.
- Pagination (`PageNumberPagination`, page size 10).
- Redis caching for high-read catalog list endpoints.
- Redis-based distributed seat locking for concurrent reservation attempts.
- Background task offloading via Celery.
- Rate limiting scopes: `anon`, `user`, `login`, `reservation`.

## Setup Instructions

### Local setup (Poetry)

1. Install Poetry
	 ```bash
	 pip install poetry
	 ```
2. Install dependencies
	 ```bash
	 poetry install --with dev
	 ```
3. Configure environment variables
	 ```bash
	 cp .env.example .env
	 ```
4. Ensure PostgreSQL and Redis are running and reachable.
5. Run migrations
	 ```bash
	 poetry run python manage.py migrate
	 ```
6. Run API
	 ```bash
	 poetry run python manage.py runserver 0.0.0.0:8000
	 ```
7. (Optional) Run Celery worker
	 ```bash
	 poetry run celery -A cinepolis_natal_api worker -l info
	 ```

### Docker setup (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Services started by Compose:
- `web` (Django API)
- `db` (PostgreSQL)
- `redis`
- `celery`

## Environment Variables

### Core

- `SECRET_KEY`: Django secret key.
- `DEBUG`: `True` or `False`.
- `ALLOWED_HOSTS`: comma-separated host list.

### Database

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

### Redis / Cache / Broker

- `REDIS_URL`
- `CACHE_KEY_PREFIX`
- `CELERY_BROKER_URL`

### JWT

- `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`
- `JWT_REFRESH_TOKEN_LIFETIME_DAYS`

### Throttling

- `THROTTLE_ANON_RATE`
- `THROTTLE_USER_RATE`
- `THROTTLE_LOGIN_RATE`
- `THROTTLE_RESERVATION_RATE`

### Email

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `EMAIL_TIMEOUT`
- `DEFAULT_FROM_EMAIL`
- `TICKET_CONFIRMATION_EMAIL_SENT_TTL_SECONDS`

### Logging

- `LOG_LEVEL`

## Running Tests

### Full test suite

- Poetry:
	```bash
	poetry run pytest -q
	```
- Docker:
	```bash
	docker compose exec web pytest -q
	```

### Integration tests

Integration tests are under `tests/integration/` and validate end-to-end API behavior, including authentication, catalog, reservation/checkout concurrency behavior, throttling, error schema, and background task-related flows.

### CI validation

The CI workflow executes:
- `python manage.py check`
- `python manage.py migrate --noinput`
- `pytest -q`
- Docker Compose config validation
- Docker image build

## Manual Testing Guide

This guide is executable with `curl`.

Base URL:
```bash
export BASE_URL="http://localhost:8000"
```

### Preconditions

- API is running.
- At least one session exists with seats in `AVAILABLE` status.
	- The API exposes endpoints for movies/sessions/rooms, but seat rows and seats are model-managed; in local environments you may create base room/seat data via admin or Django shell if needed.

Optional bootstrap via Django shell (minimal base data):

```bash
poetry run python manage.py shell
```

```python
from django.utils import timezone
from datetime import timedelta
from catalog.models import Genre, Movie, Room, Session
from reservations.models import SeatRow, Seat

genre = Genre.objects.create(name="Action")
room = Room.objects.create(name="Room 1", capacity=20)
row = SeatRow.objects.create(room=room, name="A")
seat = Seat.objects.create(row=row, number=1)

movie = Movie.objects.create(
	title="Interstellar",
	synopsis="A science fiction film.",
	duration_minutes=169,
	release_date="2014-11-07",
	poster_url="https://example.com/interstellar.jpg",
)
movie.genres.set([genre])

Session.objects.create(
	movie=movie,
	room=room,
	start_time=timezone.now() + timedelta(hours=2),
	end_time=timezone.now() + timedelta(hours=5),
)
```

### 1) Register user

```bash
curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
	-H "Content-Type: application/json" \
	-d '{
		"email": "dev1@example.com",
		"username": "dev1",
		"password": "StrongPass123!"
	}'
```

Expected: `201 Created` with user payload (no password field).

### 2) Login and capture JWT

```bash
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/" \
	-H "Content-Type: application/json" \
	-d '{"email":"dev1@example.com","password":"StrongPass123!"}')

echo "$LOGIN_RESPONSE"
export ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['access'])")
```

Expected: `200 OK` with `access` and `refresh`.

### 3) List movies

```bash
curl -s "$BASE_URL/api/v1/catalog/movies/"
```

Expected: `200 OK` paginated list (`count`, `next`, `previous`, `results`).

### 4) List sessions

```bash
curl -s "$BASE_URL/api/v1/catalog/sessions/"
```

Expected: `200 OK` with nested `movie` and `room` in each session item.

### 5) View seat map

Set target session:
```bash
export SESSION_ID="<session-uuid>"
curl -s "$BASE_URL/api/v1/reservation/sessions/$SESSION_ID/seats/"
```

Expected: `200 OK` list of seat entries with `seat_id`, `row`, `number`, `status`.

### 6) Reserve seats (temporary lock)

Set one available seat id from seat map:
```bash
export SEAT_ID="<seat-uuid>"

curl -s -X POST "$BASE_URL/api/v1/reservation/sessions/$SESSION_ID/reservations/" \
	-H "Authorization: Bearer $ACCESS_TOKEN" \
	-H "Content-Type: application/json" \
	-d "{\"seat_ids\":[\"$SEAT_ID\"]}"
```

Expected: `201 Created` with `status: TEMPORARILY_RESERVED`, `expires_at`, and reserved seats list.

### 7) Checkout (ticket generation)

```bash
curl -s -X POST "$BASE_URL/api/v1/reservation/checkout/" \
	-H "Authorization: Bearer $ACCESS_TOKEN" \
	-H "Content-Type: application/json" \
	-d "{\"session_id\":\"$SESSION_ID\",\"seat_ids\":[\"$SEAT_ID\"]}"
```

Expected: `200 OK` with `status: PURCHASED`, purchased seats, and generated ticket metadata.

### 8) List user tickets

```bash
curl -s "$BASE_URL/api/v1/users/me/tickets/" \
	-H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected: `200 OK` paginated ticket list. Optional filters:
- `/api/v1/users/me/tickets/?type=upcoming`
- `/api/v1/users/me/tickets/?type=past`

### Common error scenarios

- Invalid credentials on login: `401` with `error.code = INVALID_CREDENTIALS`
- Validation failure (missing/invalid fields): `400` with `error.code = VALIDATION_FAILED`
- Seat already reserved/purchased: `409` with `error.code = SEAT_ALREADY_RESERVED`
- Rate limiting exceeded: `429` with `error.code = THROTTLED`

## API Usage (Quick Curl Reference)

### Register

```bash
curl -X POST "$BASE_URL/api/v1/auth/register/" -H "Content-Type: application/json" -d '{"email":"dev2@example.com","username":"dev2","password":"StrongPass123!"}'
```

### Login

```bash
curl -X POST "$BASE_URL/api/v1/auth/login/" -H "Content-Type: application/json" -d '{"email":"dev2@example.com","password":"StrongPass123!"}'
```

### List movies

```bash
curl "$BASE_URL/api/v1/catalog/movies/"
```

### List sessions

```bash
curl "$BASE_URL/api/v1/catalog/sessions/"
```

### Reserve seats

```bash
curl -X POST "$BASE_URL/api/v1/reservation/sessions/$SESSION_ID/reservations/" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"seat_ids\":[\"$SEAT_ID\"]}"
```

### Checkout

```bash
curl -X POST "$BASE_URL/api/v1/reservation/checkout/" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"session_id\":\"$SESSION_ID\",\"seat_ids\":[\"$SEAT_ID\"]}"
```

### My tickets

```bash
curl "$BASE_URL/api/v1/users/me/tickets/" -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Error Handling

All API errors follow a standardized structure:

```json
{
	"error": {
		"code": "ERROR_CODE",
		"message": "Human-readable message",
		"status": 400,
		"details": {}
	}
}
```

Benefits:
- consistent error contracts across endpoints
- simpler client-side handling and observability
- safer 500 responses (internal details are not leaked)

## CI

This project currently implements Continuous Integration (CI) only. The pipeline exists to prevent regressions and keep the repository production-ready by validating code correctness, test execution, build integrity, and container reproducibility on every change to `main`, ensuring every change remains buildable, testable, and container-ready.

GitHub Actions workflow (`.github/workflows/main.yml`) includes two jobs:

1. **Validate Django API**
	 - provisions PostgreSQL + Redis services
	 - installs dependencies with Poetry
	 - runs `manage.py check`, migrations, and full tests

2. **Validate Docker build**
	 - validates Compose configuration
	 - builds application image from `Dockerfile`

Pipeline behavior:
- trigger on push and pull requests to `main`
- fail-fast per job step (any failing step fails the job)
