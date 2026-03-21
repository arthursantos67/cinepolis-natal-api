import uuid

from django.core.exceptions import ValidationError
from django.db import models


class SeatRow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        "catalog.Room",
        on_delete=models.CASCADE,
        related_name="seat_rows",
    )
    name = models.CharField(max_length=10)

    class Meta:
        db_table = "reservation_seat_rows"
        ordering = ["room", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "name"],
                name="unique_seat_row_per_room",
            )
        ]
        indexes = [
            models.Index(fields=["room"], name="seat_row_room_idx"),
        ]

    def clean(self):
        self.name = self.name.strip().upper()

        if not self.name:
            raise ValidationError({"name": "Seat row name cannot be blank."})

        if not self.name.isalpha():
            raise ValidationError(
                {"name": "Seat row name must contain letters only."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.room.name} - Row {self.name}"


class Seat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    row = models.ForeignKey(
        "reservations.SeatRow",
        on_delete=models.CASCADE,
        related_name="seats",
    )
    number = models.PositiveIntegerField()

    class Meta:
        db_table = "reservation_seats"
        ordering = ["row", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["row", "number"],
                name="unique_seat_number_per_row",
            )
        ]
        indexes = [
            models.Index(fields=["row"], name="seat_row_idx"),
        ]

    @property
    def room(self):
        return self.row.room

    def clean(self):
        if self.number <= 0:
            raise ValidationError({"number": "Seat number must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.row.room.name} - {self.row.name}{self.number}"


class SessionSeatStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    RESERVED = "RESERVED", "Reserved"
    PURCHASED = "PURCHASED", "Purchased"


class SessionSeat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "catalog.Session",
        on_delete=models.CASCADE,
        related_name="session_seats",
    )
    seat = models.ForeignKey(
        "reservations.Seat",
        on_delete=models.CASCADE,
        related_name="session_seats",
    )
    status = models.CharField(
        max_length=20,
        choices=SessionSeatStatus.choices,
        default=SessionSeatStatus.AVAILABLE,
    )
    locked_by_user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_session_seats",
    )
    lock_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reservation_session_seats"
        ordering = ["session", "seat__row__name", "seat__number"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "seat"],
                name="unique_seat_per_session",
            )
        ]
        indexes = [
            models.Index(fields=["session", "status"], name="session_status_idx"),
            models.Index(
                fields=["session", "lock_expires_at"],
                name="session_lock_expires_idx",
            ),
        ]

    def clean(self):
        if self.seat_id and self.session_id:
            if self.seat.row.room_id != self.session.room_id:
                raise ValidationError(
                    {"seat": "Seat must belong to the same room as the session."}
                )

        if self.status == SessionSeatStatus.AVAILABLE:
            if self.locked_by_user is not None:
                raise ValidationError(
                    {"locked_by_user": "Available seats cannot have a locked user."}
                )
            if self.lock_expires_at is not None:
                raise ValidationError(
                    {"lock_expires_at": "Available seats cannot have a lock expiration."}
                )

        elif self.status == SessionSeatStatus.RESERVED:
            if self.locked_by_user is None:
                raise ValidationError(
                    {"locked_by_user": "Reserved seats must have a locked user."}
                )
            if self.lock_expires_at is None:
                raise ValidationError(
                    {"lock_expires_at": "Reserved seats must have a lock expiration."}
                )

        elif self.status == SessionSeatStatus.PURCHASED:
            if self.locked_by_user is not None:
                raise ValidationError(
                    {"locked_by_user": "Purchased seats cannot have a locked user."}
                )
            if self.lock_expires_at is not None:
                raise ValidationError(
                    {"lock_expires_at": "Purchased seats cannot have a lock expiration."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.session.movie.title} | "
            f"{self.session.room.name} | "
            f"{self.seat.row.name}{self.seat.number} | "
            f"{self.status}"
        )