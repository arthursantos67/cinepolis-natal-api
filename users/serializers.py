from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import User


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