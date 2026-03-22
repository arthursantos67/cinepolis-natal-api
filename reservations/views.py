from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from cinepolis_natal_api.throttling import ReservationRateThrottle

from catalog.models import Session
from reservations.exceptions import (
    InvalidSeatSelectionError,
    SeatUnavailableError,
    SessionNotFoundError,
)
from reservations.models import SessionSeat
from reservations.serializers import (
    CheckoutRequestSerializer,
    CheckoutResponseSerializer,
    SessionSeatMapItemSerializer,
    TemporaryReservationRequestSerializer,
    TemporaryReservationResponseSerializer,
)
from reservations.services import TemporaryReservationService
from reservations.services.checkout_service import (
    ExpiredReservationError,
    InvalidSeatStateError,
    CheckoutService,
    InvalidSeatSelectionError as CheckoutInvalidSeatSelectionError,
    ReservationOwnershipError,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Reservations"],
        summary="Get session seat map",
        description="Return seat map for a specific session.",
        responses={200: SessionSeatMapItemSerializer(many=True)},
    )
)
class SessionSeatMapView(ListAPIView):
    serializer_class = SessionSeatMapItemSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        session = get_object_or_404(Session, id=self.kwargs["session_id"])

        return (
            SessionSeat.objects.select_related("seat", "seat__row")
            .filter(session=session)
            .order_by("seat__row__name", "seat__number")
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Reservations"],
        summary="Create temporary reservation",
        description="Temporarily reserve seats for the authenticated user.",
        request=TemporaryReservationRequestSerializer,
        responses={
            201: TemporaryReservationResponseSerializer,
            400: OpenApiResponse(description="Validation error."),
            404: OpenApiResponse(description="Session not found."),
            409: OpenApiResponse(description="Seat unavailable."),
            429: OpenApiResponse(description="Too many reservation attempts."),
        },
    )
)
class TemporarySeatReservationView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TemporaryReservationRequestSerializer
    throttle_classes = [ReservationRateThrottle]

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


@extend_schema_view(
    post=extend_schema(
        tags=["Reservations"],
        summary="Checkout reserved seats",
        description="Finalize the purchase for temporarily reserved seats.",
        request=CheckoutRequestSerializer,
        responses={
            200: CheckoutResponseSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Reservation ownership error."),
            409: OpenApiResponse(description="Reservation expired or invalid seat state."),
            429: OpenApiResponse(description="Too many checkout attempts."),
        },
    )
)
class CheckoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutRequestSerializer
    throttle_classes = [ReservationRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = CheckoutService()

        try:
            checkout_result = service.execute(
                session_id=serializer.validated_data["session_id"],
                seat_ids=serializer.validated_data["seat_ids"],
                user=request.user,
            )
        except CheckoutInvalidSeatSelectionError as exc:
            raise ValidationError(detail={"seat_ids": [str(exc)]}) from exc
        except ReservationOwnershipError as exc:
            return Response(
                {
                    "error": "RESERVATION_OWNERSHIP_ERROR",
                    "message": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ExpiredReservationError as exc:
            return Response(
                {
                    "error": "RESERVATION_EXPIRED",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InvalidSeatStateError as exc:
            return Response(
                {
                    "error": "INVALID_SEAT_STATE",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        response_serializer = CheckoutResponseSerializer(checkout_result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)