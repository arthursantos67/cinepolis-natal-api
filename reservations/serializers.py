from rest_framework import serializers

from reservations.models import SessionSeat


class SessionSeatMapItemSerializer(serializers.ModelSerializer):
    seat_id = serializers.UUIDField(source="seat.id", read_only=True)
    row = serializers.CharField(source="seat.row.name", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)

    class Meta:
        model = SessionSeat
        fields = ["seat_id", "row", "number", "status"]