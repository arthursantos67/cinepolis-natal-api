from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from catalog.models import Session
from reservations.models import SessionSeat
from reservations.serializers import SessionSeatMapItemSerializer


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