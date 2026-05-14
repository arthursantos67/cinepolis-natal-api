from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from users.models import User
from reservations.models import Ticket


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_email(self, value):
        return User.objects.normalize_email(value)

    def validate_username(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("This field may not be blank.")

        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        return User.objects.normalize_email(value)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if user is None:
            raise AuthenticationFailed("Invalid credentials.")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        attrs["user"] = user
        return attrs


class UserTicketSessionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()


class UserTicketMovieSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    poster_url = serializers.URLField(allow_null=True)


class UserTicketSeatSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    row = serializers.CharField()
    number = serializers.IntegerField()


class UserTicketSerializer(serializers.ModelSerializer):
    ticket_id = serializers.UUIDField(source="id")
    ticket_code = serializers.CharField()
    created_at = serializers.DateTimeField()

    session = serializers.SerializerMethodField()
    movie = serializers.SerializerMethodField()
    seat = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            "ticket_id",
            "ticket_code",
            "created_at",
            "session",
            "movie",
            "seat",
        )

    @extend_schema_field(UserTicketSessionSerializer)
    def get_session(self, obj):
        session = obj.session_seat.session
        return {
            "id": str(session.id),
            "start_time": session.start_time,
            "end_time": session.end_time,
        }

    @extend_schema_field(UserTicketMovieSerializer)
    def get_movie(self, obj):
        movie = obj.session_seat.session.movie
        return {
            "id": str(movie.id),
            "title": movie.title,
            "poster_url": movie.poster_url,
        }

    @extend_schema_field(UserTicketSeatSerializer)
    def get_seat(self, obj):
        seat = obj.session_seat.seat
        return {
            "id": str(seat.id),
            "row": seat.row.name,
            "number": seat.number,
        }