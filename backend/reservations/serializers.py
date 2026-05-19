from rest_framework import serializers

from reservations.models import Seat, SeatRow, SessionSeat, Ticket


class SeatRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatRow
        fields = ["id", "room", "name"]
        read_only_fields = ["id"]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "row", "number", "is_accessible"]
        read_only_fields = ["id"]


class SessionSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionSeat
        fields = [
            "id",
            "session",
            "seat",
            "status",
            "locked_by_user",
            "lock_expires_at",
        ]
        read_only_fields = ["id"]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "user", "session_seat", "ticket_code", "created_at"]
        read_only_fields = ["id", "ticket_code", "created_at"]


class SessionSeatMapItemSerializer(serializers.ModelSerializer):
    session_seat_id = serializers.UUIDField(source="id", read_only=True)
    seat_id = serializers.UUIDField(source="seat.id", read_only=True)
    row = serializers.CharField(source="seat.row.name", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)
    is_accessible = serializers.BooleanField(
        source="seat.is_accessible", read_only=True
    )
    reserved_by_current_user = serializers.SerializerMethodField()
    lock_expires_at = serializers.SerializerMethodField()

    class Meta:
        model = SessionSeat
        fields = [
            "session_seat_id",
            "seat_id",
            "row",
            "number",
            "status",
            "is_accessible",
            "reserved_by_current_user",
            "lock_expires_at",
        ]

    def get_reserved_by_current_user(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return bool(
            user
            and user.is_authenticated
            and obj.status == "RESERVED"
            and obj.locked_by_user_id == user.id
        )

    def get_lock_expires_at(self, obj):
        if not self.get_reserved_by_current_user(obj):
            return None

        return obj.lock_expires_at

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            data.pop("reserved_by_current_user", None)
            data.pop("lock_expires_at", None)

        return data


class TemporaryReservationRequestSerializer(serializers.Serializer):
    seat_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_seat_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Seat IDs must be unique.")
        return value


class TemporaryReservationReleaseRequestSerializer(serializers.Serializer):
    session_seat_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_session_seat_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Session seat IDs must be unique.")
        return value


class TemporaryReservationSeatSerializer(serializers.ModelSerializer):
    seat_id = serializers.UUIDField(source="seat.id", read_only=True)
    row = serializers.CharField(source="seat.row.name", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)

    class Meta:
        model = SessionSeat
        fields = ["seat_id", "row", "number", "status"]


class TemporaryReservationResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    status = serializers.CharField()
    expires_at = serializers.DateTimeField()
    seats = TemporaryReservationSeatSerializer(many=True)


class TemporaryReservationReleaseSeatSerializer(serializers.ModelSerializer):
    session_seat_id = serializers.UUIDField(source="id", read_only=True)
    seat_id = serializers.UUIDField(source="seat.id", read_only=True)
    row = serializers.CharField(source="seat.row.name", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)
    is_accessible = serializers.BooleanField(
        source="seat.is_accessible", read_only=True
    )

    class Meta:
        model = SessionSeat
        fields = [
            "session_seat_id",
            "seat_id",
            "row",
            "number",
            "status",
            "is_accessible",
        ]


class TemporaryReservationReleaseResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    status = serializers.CharField()
    seats = TemporaryReservationReleaseSeatSerializer(many=True)


class CheckoutRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    seat_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_seat_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Seat IDs must be unique.")
        return value


class CheckoutSeatResponseSerializer(serializers.Serializer):
    seat_id = serializers.UUIDField()
    row = serializers.CharField()
    number = serializers.IntegerField()
    status = serializers.CharField()


class CheckoutResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    session_id = serializers.UUIDField()
    seats = CheckoutSeatResponseSerializer(many=True)
