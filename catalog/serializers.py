from rest_framework import serializers

from django.db import transaction

from catalog.models import Genre, Movie, Room, Session
from reservations.models import SessionSeat, Seat


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class GenreSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity"]


class MovieWriteSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
    )

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "genres",
            "synopsis",
            "duration_minutes",
            "release_date",
            "poster_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MovieReadSerializer(serializers.ModelSerializer):
    genres = GenreSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "genres",
            "synopsis",
            "duration_minutes",
            "release_date",
            "poster_url",
            "created_at",
            "updated_at",
        ]


class MovieSummarySerializer(serializers.ModelSerializer):
    genres = GenreSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "genres",
            "duration_minutes",
            "release_date",
            "poster_url",
        ]


class SessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            "id",
            "movie",
            "room",
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        session = Session.objects.create(**validated_data)

        seats = Seat.objects.select_related("row").filter(row__room=session.room)

        session_seats = [
            SessionSeat(session=session, seat=seat)
            for seat in seats
        ]

        SessionSeat.objects.bulk_create(session_seats)

        return session


class SessionReadSerializer(serializers.ModelSerializer):
    movie = MovieSummarySerializer(read_only=True)
    room = RoomSummarySerializer(read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "movie",
            "room",
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ]