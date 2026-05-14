import pytest
from datetime import timedelta
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Genre, Movie, Room, Session


@pytest.mark.django_db
class TestCatalogApi:
    @pytest.fixture(autouse=True)
    def clear_cache_between_tests(self):
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def genre(self):
        return Genre.objects.create(name="Drama")

    @pytest.fixture
    def second_genre(self):
        return Genre.objects.create(name="Crime")

    @pytest.fixture
    def movie(self, genre, second_genre):
        movie = Movie.objects.create(
            title="The Godfather",
            synopsis="Crime family drama.",
            duration_minutes=175,
            release_date="1972-07-07",
            poster_url="https://example.com/godfather.jpg",
        )
        movie.genres.set([genre, second_genre])
        return movie

    @pytest.fixture
    def room(self):
        return Room.objects.create(
            name="Room 1",
            capacity=70,
        )

    @pytest.fixture
    def session(self, movie, room):
        return Session.objects.create(
            movie=movie,
            room=room,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=3, minutes=55),
        )

    def test_list_genres_returns_200(self, api_client, genre):
        response = api_client.get("/api/v1/catalog/genres/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == genre.name

    def test_create_genre_returns_201(self, api_client):
        response = api_client.post(
            "/api/v1/catalog/genres/",
            {"name": "Sci-Fi"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Sci-Fi"
        assert Genre.objects.filter(name="Sci-Fi").exists()

    def test_list_movies_returns_200_with_nested_genres(self, api_client, movie):
        response = api_client.get("/api/v1/catalog/movies/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == movie.title
        assert len(response.data["results"][0]["genres"]) == 2
        assert "name" in response.data["results"][0]["genres"][0]

    def test_create_movie_returns_201(self, api_client, genre, second_genre):
        response = api_client.post(
            "/api/v1/catalog/movies/",
            {
                "title": "Interstellar",
                "genres": [str(genre.id), str(second_genre.id)],
                "synopsis": "Space exploration.",
                "duration_minutes": 169,
                "release_date": "2014-11-07",
                "poster_url": "https://example.com/interstellar.jpg",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Movie.objects.filter(title="Interstellar").exists()

    def test_list_rooms_returns_200(self, api_client, room):
        response = api_client.get("/api/v1/catalog/rooms/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == room.name

    def test_create_room_returns_201(self, api_client):
        response = api_client.post(
            "/api/v1/catalog/rooms/",
            {
                "name": "Room 2",
                "capacity": 80,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Room 2"
        assert Room.objects.filter(name="Room 2").exists()

    def test_list_sessions_returns_200_with_nested_movie_and_room(
        self,
        api_client,
        session,
    ):
        response = api_client.get("/api/v1/catalog/sessions/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["movie"]["title"] == session.movie.title
        assert response.data["results"][0]["room"]["name"] == session.room.name

    def test_create_session_returns_201(self, api_client, movie, room):
        response = api_client.post(
            "/api/v1/catalog/sessions/",
            {
                "movie": str(movie.id),
                "room": str(room.id),
                "start_time": "2026-03-23T18:00:00Z",
                "end_time": "2026-03-23T20:55:00Z",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Session.objects.count() == 1

    def test_delete_genre_returns_204(self, api_client, genre):
        response = api_client.delete(f"/api/v1/catalog/genres/{genre.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Genre.objects.filter(id=genre.id).exists()

    def test_update_genre_returns_200(self, api_client, genre, movie):
        response = api_client.patch(
            f"/api/v1/catalog/genres/{genre.id}/",
            {"name": "Drama Updated"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Drama Updated"
        genre.refresh_from_db()
        assert genre.name == "Drama Updated"
        movie.refresh_from_db()
        assert movie.genres.filter(name="Drama Updated").exists()

    def test_update_movie_returns_200(self, api_client, movie):
        response = api_client.patch(
            f"/api/v1/catalog/movies/{movie.id}/",
            {"title": "The Godfather Remastered"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        movie.refresh_from_db()
        assert movie.title == "The Godfather Remastered"

    def test_update_room_returns_200(self, api_client, room):
        response = api_client.patch(
            f"/api/v1/catalog/rooms/{room.id}/",
            {"name": "Room Prime", "capacity": 90},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Room Prime"
        assert response.data["capacity"] == 90
        room.refresh_from_db()
        assert room.name == "Room Prime"
        assert room.capacity == 90

    def test_update_session_returns_200(self, api_client, session):
        new_end_time = (session.end_time + timedelta(minutes=30)).isoformat().replace(
            "+00:00",
            "Z",
        )

        response = api_client.patch(
            f"/api/v1/catalog/sessions/{session.id}/",
            {"end_time": new_end_time},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        session.refresh_from_db()
        assert session.end_time == timezone.datetime.fromisoformat(
            new_end_time.replace("Z", "+00:00")
        )

    def test_update_session_should_reject_room_change(self, api_client, session):
        other_room = Room.objects.create(name="Room 2", capacity=80)

        response = api_client.patch(
            f"/api/v1/catalog/sessions/{session.id}/",
            {"room": str(other_room.id)},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"]["code"] == "VALIDATION_FAILED"
        assert "room" in response.data["error"]["details"]
        
    def test_list_movies_should_use_cache_on_second_request(self, api_client, movie):
        cache.clear()

        with CaptureQueriesContext(connection) as first_request_queries:
            first_response = api_client.get("/api/v1/catalog/movies/")

        with CaptureQueriesContext(connection) as second_request_queries:
            second_response = api_client.get("/api/v1/catalog/movies/")

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK
        assert first_response.data == second_response.data
        assert len(second_request_queries) < len(first_request_queries)
        
    def test_list_sessions_should_use_cache_on_second_request(self, api_client, session):
        cache.clear()

        with CaptureQueriesContext(connection) as first_request_queries:
            first_response = api_client.get("/api/v1/catalog/sessions/")

        with CaptureQueriesContext(connection) as second_request_queries:
            second_response = api_client.get("/api/v1/catalog/sessions/")

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK
        assert first_response.data == second_response.data
        assert len(second_request_queries) < len(first_request_queries)
        
    def test_movie_list_cache_should_be_invalidated_after_movie_creation(
        self,
        api_client,
        genre,
        second_genre,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/movies/")
        assert first_response.status_code == status.HTTP_200_OK
        initial_count = first_response.data["count"]

        create_response = api_client.post(
            "/api/v1/catalog/movies/",
            {
                "title": "Interstellar",
                "genres": [str(genre.id), str(second_genre.id)],
                "synopsis": "Space exploration.",
                "duration_minutes": 169,
                "release_date": "2014-11-07",
                "poster_url": "https://example.com/interstellar.jpg",
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        second_response = api_client.get("/api/v1/catalog/movies/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["count"] == initial_count + 1
        
    def test_session_list_cache_should_be_invalidated_after_session_creation(
        self,
        api_client,
        movie,
        room,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/sessions/")
        assert first_response.status_code == status.HTTP_200_OK
        initial_count = first_response.data["count"]

        create_response = api_client.post(
            "/api/v1/catalog/sessions/",
            {
                "movie": str(movie.id),
                "room": str(room.id),
                "start_time": "2026-03-23T18:00:00Z",
                "end_time": "2026-03-23T20:55:00Z",
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        second_response = api_client.get("/api/v1/catalog/sessions/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["count"] == initial_count + 1
        
    def test_movie_list_cache_should_be_invalidated_after_movie_deletion(
        self,
        api_client,
        movie,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/movies/")
        assert first_response.status_code == status.HTTP_200_OK
        initial_count = first_response.data["count"]

        delete_response = api_client.delete(f"/api/v1/catalog/movies/{movie.id}/")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        second_response = api_client.get("/api/v1/catalog/movies/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["count"] == initial_count - 1

    def test_genre_update_should_invalidate_movie_and_session_list_caches(
        self,
        api_client,
        genre,
        session,
    ):
        cache.clear()

        first_movie_response = api_client.get("/api/v1/catalog/movies/")
        first_session_response = api_client.get("/api/v1/catalog/sessions/")

        assert first_movie_response.status_code == status.HTTP_200_OK
        assert first_session_response.status_code == status.HTTP_200_OK
        assert first_movie_response.data["results"][0]["genres"][0]["name"] == "Crime"

        update_response = api_client.patch(
            f"/api/v1/catalog/genres/{genre.id}/",
            {"name": "Drama Updated"},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK

        second_movie_response = api_client.get("/api/v1/catalog/movies/")
        second_session_response = api_client.get("/api/v1/catalog/sessions/")

        assert second_movie_response.status_code == status.HTTP_200_OK
        assert second_session_response.status_code == status.HTTP_200_OK
        movie_genre_names = [
            item["name"]
            for item in second_movie_response.data["results"][0]["genres"]
        ]
        session_genre_names = [
            item["name"]
            for item in second_session_response.data["results"][0]["movie"]["genres"]
        ]
        assert "Drama Updated" in movie_genre_names
        assert "Drama Updated" in session_genre_names

    def test_movie_update_should_invalidate_movie_and_session_list_caches(
        self,
        api_client,
        movie,
        session,
    ):
        cache.clear()

        first_movie_response = api_client.get("/api/v1/catalog/movies/")
        first_session_response = api_client.get("/api/v1/catalog/sessions/")

        assert first_movie_response.status_code == status.HTTP_200_OK
        assert first_session_response.status_code == status.HTTP_200_OK

        update_response = api_client.patch(
            f"/api/v1/catalog/movies/{movie.id}/",
            {"title": "The Godfather Updated"},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK

        second_movie_response = api_client.get("/api/v1/catalog/movies/")
        second_session_response = api_client.get("/api/v1/catalog/sessions/")

        assert second_movie_response.status_code == status.HTTP_200_OK
        assert second_session_response.status_code == status.HTTP_200_OK
        assert second_movie_response.data["results"][0]["title"] == "The Godfather Updated"
        assert (
            second_session_response.data["results"][0]["movie"]["title"]
            == "The Godfather Updated"
        )

    def test_session_list_cache_should_be_invalidated_after_session_deletion(
        self,
        api_client,
        session,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/sessions/")
        assert first_response.status_code == status.HTTP_200_OK
        initial_count = first_response.data["count"]

        delete_response = api_client.delete(
            f"/api/v1/catalog/sessions/{session.id}/"
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        second_response = api_client.get("/api/v1/catalog/sessions/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["count"] == initial_count - 1

    def test_room_update_should_invalidate_session_list_cache(
        self,
        api_client,
        room,
        session,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/sessions/")
        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data["results"][0]["room"]["name"] == "Room 1"

        update_response = api_client.patch(
            f"/api/v1/catalog/rooms/{room.id}/",
            {"name": "Room Prime", "capacity": 70},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK

        second_response = api_client.get("/api/v1/catalog/sessions/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["results"][0]["room"]["name"] == "Room Prime"

    def test_session_update_should_invalidate_session_list_cache(
        self,
        api_client,
        session,
    ):
        cache.clear()

        first_response = api_client.get("/api/v1/catalog/sessions/")
        assert first_response.status_code == status.HTTP_200_OK

        new_end_time = (session.end_time + timedelta(minutes=30)).isoformat().replace(
            "+00:00",
            "Z",
        )

        update_response = api_client.patch(
            f"/api/v1/catalog/sessions/{session.id}/",
            {"end_time": new_end_time},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK

        second_response = api_client.get("/api/v1/catalog/sessions/")
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["results"][0]["end_time"] == new_end_time
