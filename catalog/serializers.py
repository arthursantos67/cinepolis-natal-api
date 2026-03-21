from rest_framework import serializers

from catalog.models import Genre, Movie, Room, Session


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