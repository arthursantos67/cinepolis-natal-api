from django.utils import timezone
from rest_framework.generics import CreateAPIView, ListAPIView

from reservations.models import Ticket
from users.serializers import (
    UserLoginSerializer,
    UserRegistrationSerializer,
    UserTicketSerializer,
)

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import UserLoginSerializer, UserRegistrationSerializer


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "id": str(request.user.id),
                "email": request.user.email,
                "username": request.user.username,
                "created_at": request.user.created_at,
            },
            status=status.HTTP_200_OK,
        )
        
class MyTicketsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserTicketSerializer

    def get_queryset(self):
        queryset = (
            Ticket.objects.filter(user=self.request.user)
            .select_related(
                "session_seat__session__movie",
                "session_seat__seat__row",
            )
            .order_by("-created_at")
        )

        ticket_type = self.request.query_params.get("type")
        now = timezone.now()

        if ticket_type == "upcoming":
            queryset = queryset.filter(session_seat__session__start_time__gt=now)
        elif ticket_type == "past":
            queryset = queryset.filter(session_seat__session__start_time__lte=now)

        return queryset