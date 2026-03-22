from rest_framework import serializers

from reservations.models import SessionSeat


class SessionSeatMapItemSerializer(serializers.ModelSerializer):
    seat_id = serializers.UUIDField(source="seat.id", read_only=True)
    row = serializers.CharField(source="seat.row.name", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)

    class Meta:
        model = SessionSeat
        fields = ["seat_id", "row", "number", "status"]


class TemporaryReservationRequestSerializer(serializers.Serializer):
    seat_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_seat_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Seat IDs must be unique.")
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