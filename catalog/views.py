from django.core.cache import cache
from django_redis import get_redis_connection
from rest_framework.response import Response
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

def invalidate_movie_list_cache():
    redis = get_redis_connection("default")
    for key in redis.scan_iter("*catalog:movies:*"):
        redis.delete(key)


def invalidate_session_list_cache():
    redis = get_redis_connection("default")
    for key in redis.scan_iter("*catalog:sessions:*"):
        redis.delete(key)

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
    CACHE_TTL_SECONDS = 300

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MovieReadSerializer
        return MovieWriteSerializer

    def list(self, request, *args, **kwargs):
        cache_key = f"catalog:movies:{request.get_full_path()}"
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.CACHE_TTL_SECONDS)
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        invalidate_movie_list_cache()
        return response


class MovieDetailView(RetrieveDestroyAPIView):
    queryset = Movie.objects.prefetch_related("genres").all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MovieReadSerializer
        return MovieWriteSerializer

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        invalidate_movie_list_cache()
        return response


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
    CACHE_TTL_SECONDS = 300

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SessionReadSerializer
        return SessionWriteSerializer

    def list(self, request, *args, **kwargs):
        cache_key = f"catalog:sessions:{request.get_full_path()}"
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.CACHE_TTL_SECONDS)
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        invalidate_session_list_cache()
        return response


class SessionDetailView(RetrieveDestroyAPIView):
    queryset = Session.objects.select_related("movie", "room").prefetch_related(
        "movie__genres"
    ).all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SessionReadSerializer
        return SessionWriteSerializer

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        invalidate_session_list_cache()
        return response