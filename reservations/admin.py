from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Seat, SeatRow, SessionSeat

class SessionSeatAdminForm(forms.ModelForm):
    class Meta:
        model = SessionSeat
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get("session")
        seat = cleaned_data.get("seat")

        if session and seat and seat.row.room_id != session.room_id:
            raise ValidationError(
                "Selected seat must belong to the same room as the session."
            )

        return cleaned_data


@admin.register(SeatRow)
class SeatRowAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "name")
    search_fields = ("name", "room__name")
    list_filter = ("room",)


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("id", "row", "room", "number")
    search_fields = ("row__name", "row__room__name")
    list_filter = ("row__room",)

    @admin.display(ordering="row__room__name", description="Room")
    def room(self, obj):
        return obj.row.room.name


@admin.register(SessionSeat)
class SessionSeatAdmin(admin.ModelAdmin):
    form = SessionSeatAdminForm
    list_display = (
        "id",
        "session",
        "seat",
        "room",
        "status",
        "locked_by_user",
        "lock_expires_at",
    )
    list_filter = ("status", "session__room", "session__movie")
    search_fields = (
        "seat__row__name",
        "session__movie__title",
        "session__room__name",
    )
    ordering = ("session__start_time", "seat__row__name", "seat__number")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "session":
            kwargs["queryset"] = (
                db_field.related_model.objects.select_related("movie", "room")
                .order_by("movie__title", "start_time")
            )
        elif db_field.name == "seat":
            kwargs["queryset"] = (
                db_field.related_model.objects.select_related("row", "row__room")
                .order_by("row__room__name", "row__name", "number")
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(ordering="session__room__name", description="Room")
    def room(self, obj):
        return obj.session.room.name