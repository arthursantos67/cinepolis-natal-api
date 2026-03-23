# Cinepolis Natal API

## Software Requirements Specification (Implementation-Aligned)

**Project:** cinepolis-natal-api  
**Document type:** Software Requirements Specification (SRS)  
**Version:** 1.0  
**Last update:** 2026-03-22

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [System Context](#2-system-context)
3. [Architecture Overview](#3-architecture-overview)
4. [Functional Requirements](#4-functional-requirements)
5. [Use Cases (1–7)](#5-use-cases-17)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Model and Integrity Rules](#7-data-model-and-integrity-rules)
8. [API Contract and Error Standard](#8-api-contract-and-error-standard)
9. [Security and Access Control](#9-security-and-access-control)
10. [Operational Requirements](#10-operational-requirements)
11. [Requirements Traceability Matrix](#11-requirements-traceability-matrix)
12. [Out of Scope](#12-out-of-scope)

---

## 1. Purpose and Scope

The Cinepolis Natal API is a production-oriented REST backend for cinema reservation operations.

Scope covered by this implementation:
- user registration and JWT authentication
- public catalog browsing (genres, movies, rooms, sessions)
- session seat map inspection
- temporary seat reservation with lock expiration
- checkout and ticket generation
- authenticated user ticket listing
- standardized API error responses
- rate limiting, health checks, background processing, and automated CI validation

The system targets backend API consumption only.

## 2. System Context

### 2.1 Business context

The API supports a movie reservation process where users must be able to reserve seats safely under concurrent access.

### 2.2 Actors

| Actor | Description | Capabilities |
| --- | --- | --- |
| Visitor | Unauthenticated consumer | Browse catalog and seat map, register, login |
| Authenticated User | User with valid JWT access token | Temporary reservation, checkout, view own tickets, view own profile |

## 3. Architecture Overview

### 3.1 Architectural style

Modular monolith built with Django and Django REST Framework.

### 3.2 Core components

- **API layer:** DRF views and serializers.
- **Domain/data layer:** Django ORM models with relational constraints.
- **Service layer:** reservation, checkout, and expiration services.
- **Infrastructure:** PostgreSQL, Redis, Celery worker.

### 3.3 Redis responsibilities

- list caching for catalog endpoints
- distributed seat locking (`lock:session-seat:{session_id}:{seat_id}`)

### 3.4 Celery responsibilities

- release expired temporary reservations
- send ticket confirmation emails asynchronously

### 3.5 Error handling model

- centralized exception handler
- consistent error envelope across API endpoints
- internal errors sanitized in responses and logged with context

## 4. Functional Requirements

### FR-01 User Registration

The system shall allow account creation with `email`, `username`, and `password`.

### FR-02 User Login

The system shall authenticate users using email/password and issue JWT access and refresh tokens.

### FR-03 Current User Data

The system shall expose an authenticated endpoint to retrieve the current user profile.

### FR-04 Catalog Endpoints

The system shall provide endpoints for genres, movies, rooms, and sessions with list/create/retrieve/delete operations. In the current implementation, all these catalog operations are public (`AllowAny`), including create and delete. Update operations are not implemented.

### FR-05 Seat Map Visualization

The system shall provide public session seat maps with per-seat status (`AVAILABLE`, `RESERVED`, `PURCHASED`).

### FR-06 Temporary Reservation

The system shall allow authenticated users to temporarily reserve session seats, enforcing seat availability and ownership metadata.

### FR-07 Reservation Expiration

The system shall expire temporary seat reservations after 600 seconds and restore seat availability when expired.

### FR-08 Checkout

The system shall finalize valid reserved seats into purchased seats in a transactional operation and generate tickets.

### FR-09 My Tickets

The system shall allow authenticated users to list their own tickets, with optional `type=upcoming|past` filtering.

### FR-10 API Documentation Endpoints

The system shall expose OpenAPI schema and Swagger UI.

### FR-11 Health Check

The system shall expose a health endpoint verifying database, Redis, and Celery connectivity.

## 5. Use Cases (1–7)

### UC-1 Register User

**Actor:** Visitor  
**Precondition:** none  
**Main flow:** submit registration payload; system validates and creates user.  
**Result:** user account created.

### UC-2 Login User

**Actor:** Visitor  
**Precondition:** registered account exists  
**Main flow:** submit credentials; system authenticates and returns JWT tokens.  
**Result:** user can access protected endpoints.

### UC-3 List Movies

**Actor:** Visitor or Authenticated User  
**Main flow:** call movies list endpoint; system returns paginated results (with caching when available).

### UC-4 List Sessions

**Actor:** Visitor or Authenticated User  
**Main flow:** call sessions list endpoint; system returns paginated session data with movie and room details.

### UC-5 View Session Seat Map

**Actor:** Visitor or Authenticated User  
**Main flow:** request session seat map; system returns all seats and statuses.

### UC-6 Reserve and Checkout Seats

**Actor:** Authenticated User  
**Main flow:** reserve available seats temporarily; before expiration, checkout those seats; system marks seats purchased and creates tickets.

### UC-7 View My Tickets

**Actor:** Authenticated User  
**Main flow:** request own ticket list (optionally filtered by upcoming/past).  
**Result:** paginated ticket data bound to authenticated user.

## 6. Non-Functional Requirements

### NFR-01 Performance and response behavior

- list endpoints are paginated
- movies/sessions list endpoints use Redis-backed caching

### NFR-02 Concurrency and consistency

- distributed lock prevents competing seat reservation attempts
- checkout runs in a DB transaction
- seat status transitions are validated and persisted consistently

### NFR-03 Reliability

- expiration and email tasks executed asynchronously
- email task has retry behavior for transient failures

### NFR-04 Security

- JWT authentication for protected operations
- password validation in registration serializer
- access control via DRF permissions

### NFR-05 Abuse protection

- global anonymous and authenticated throttles
- endpoint-specific throttles for login and reservation operations

### NFR-06 Operability

- structured logging
- correlation ID middleware
- health check endpoint

### NFR-07 Testability

- automated test suite with integration coverage for core business flows and error contracts

## 7. Data Model and Integrity Rules

Primary entities:
- `User`
- `Genre`
- `Movie`
- `Room`
- `Session`
- `SeatRow`
- `Seat`
- `SessionSeat`
- `Ticket`

Key integrity rules implemented:
- unique movie constraint: `(title, release_date)`
- room capacity and movie duration check constraints
- no overlapping sessions in the same room (DB exclusion constraint + model validation)
- unique seat coordinates (`row`, `number`) and unique seat per session
- `SessionSeat` validation across status/lock fields
- ticket only for purchased seat (`OneToOne` with `SessionSeat`)

## 8. API Contract and Error Standard

### 8.1 Base endpoints

- `GET /health/`
- `GET /api/schema/`
- `GET /api/docs/`
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `GET /api/v1/auth/me/`
- `GET /api/v1/users/me/`
- `GET /api/v1/users/me/tickets/`
- `GET/POST/DELETE /api/v1/catalog/...`
- `GET /api/v1/reservation/sessions/{session_id}/seats/`
- `POST /api/v1/reservation/sessions/{session_id}/reservations/`
- `POST /api/v1/reservation/checkout/`

### 8.2 Standardized error payload

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

Error codes in active use include:
- `VALIDATION_FAILED`
- `INVALID_CREDENTIALS`
- `NOT_AUTHENTICATED`
- `PERMISSION_DENIED`
- `RESOURCE_NOT_FOUND`
- `SEAT_ALREADY_RESERVED`
- `THROTTLED`
- `INTERNAL_SERVER_ERROR`

## 9. Security and Access Control

- JWT Bearer authentication is the default API auth mechanism.
- Catalog and health endpoints are public.
- Catalog mutation operations (`POST` and `DELETE` on catalog resources) are also public in the current implementation and should be exposed only in controlled deployment contexts.
- Reservation, checkout, current-user, and ticket endpoints require authentication.
- Login and reservation endpoints have dedicated throttle scopes.

## 10. Operational Requirements

### 10.1 Deployment/runtime

- Docker Compose stack includes web, db, redis, celery services.
- Environment variables control DB, Redis, JWT lifetimes, throttling, email, and logging behavior.

### 10.2 CI requirements

GitHub Actions pipeline validates:
- dependency installation via Poetry
- Django system check
- migrations
- test suite execution
- Docker Compose configuration
- Docker image build

## 11. Requirements Traceability Matrix

| Requirement | Implementation artifact |
| --- | --- |
| FR-01 | `users.views.UserRegistrationView`, `users.serializers.UserRegistrationSerializer` |
| FR-02 | `users.views.UserLoginView`, `users.serializers.UserLoginSerializer` |
| FR-03 | `users.views.CurrentUserView` |
| FR-04 | `catalog.views.*`, `catalog.urls` |
| FR-05 | `reservations.views.SessionSeatMapView` |
| FR-06 | `reservations.views.TemporarySeatReservationView`, `reservations.services.TemporaryReservationService` |
| FR-07 | `reservations.tasks.release_expired_session_seat`, `reservations.services.ExpiredSeatReleaseService` |
| FR-08 | `reservations.views.CheckoutView`, `reservations.services.CheckoutService`, `reservations.models.Ticket` |
| FR-09 | `users.views.MyTicketsView` |
| FR-10 | `cinepolis_natal_api.urls` (`/api/schema/`, `/api/docs/`) |
| FR-11 | `cinepolis_natal_api.health.HealthCheckService`, `/health/` |

## 12. Out of Scope

Not implemented in this project scope:
- payment gateway processing
- frontend or mobile applications
- seat/row CRUD API endpoints
- role-based administration workflows beyond Django admin
