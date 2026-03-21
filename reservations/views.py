from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalog.models import Session
from reservations.exceptions import (
    InvalidSeatSelectionError,
    SeatUnavailableError,
    SessionNotFoundError,
)
from reservations.models import SessionSeat
from reservations.serializers import (
    SessionSeatMapItemSerializer,
    TemporaryReservationRequestSerializer,
    TemporaryReservationResponseSerializer,
)
from reservations.services import TemporaryReservationService


class SessionSeatMapView(ListAPIView):
    serializer_class = SessionSeatMapItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        session = get_object_or_404(Session, id=self.kwargs["session_id"])

        return (
            SessionSeat.objects.select_related("seat", "seat__row")
            .filter(session=session)
            .order_by("seat__row__name", "seat__number")
        )


class TemporarySeatReservationView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TemporaryReservationRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = TemporaryReservationService()

        try:
            reservation_result = service.execute(
                session_id=self.kwargs["session_id"],
                seat_ids=serializer.validated_data["seat_ids"],
                user=request.user,
            )
        except SessionNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except InvalidSeatSelectionError as exc:
            raise ValidationError(detail={"seat_ids": [str(exc)]}) from exc
        except SeatUnavailableError as exc:
            return Response(
                {
                    "error": "SEAT_UNAVAILABLE",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        response_payload = {
            "session_id": reservation_result["session_id"],
            "status": reservation_result["status"],
            "expires_at": reservation_result["expires_at"],
            "seats": reservation_result["seats"],
        }

        response_serializer = TemporaryReservationResponseSerializer(
            response_payload
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)