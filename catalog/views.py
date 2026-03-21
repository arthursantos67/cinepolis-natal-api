from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import AllowAny

from catalog.models import Genre, Movie, Room, Session
from catalog.serializers import (
    GenreSerializer,
    MovieReadSerializer,
    MovieWriteSerializer,
    RoomSerializer,
    SessionReadSerializer,
    SessionWriteSerializer,
)


class GenreListCreateView(ListCreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class GenreDetailView(RetrieveDestroyAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class MovieListCreateView(ListCreateAPIView):
    queryset = Movie.objects.prefetch_related("genres").all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MovieReadSerializer
        return MovieWriteSerializer


class MovieDetailView(RetrieveDestroyAPIView):
    queryset = Movie.objects.prefetch_related("genres").all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MovieReadSerializer
        return MovieWriteSerializer


class RoomListCreateView(ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]


class RoomDetailView(RetrieveDestroyAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]


class SessionListCreateView(ListCreateAPIView):
    queryset = Session.objects.select_related("movie", "room").prefetch_related(
        "movie__genres"
    ).all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SessionReadSerializer
        return SessionWriteSerializer


class SessionDetailView(RetrieveDestroyAPIView):
    queryset = Session.objects.select_related("movie", "room").prefetch_related(
        "movie__genres"
    ).all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SessionReadSerializer
        return SessionWriteSerializer