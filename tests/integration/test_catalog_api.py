import pytest
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Genre, Movie, Room, Session


@pytest.mark.django_db
class TestCatalogApi:
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
            start_time="2026-03-22T18:00:00Z",
            end_time="2026-03-22T20:55:00Z",
        )

    def test_list_genres_returns_200(self, api_client, genre):
        response = api_client.get("/api/v1/catalog/genres/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == genre.name

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
        assert len(response.data) == 1
        assert response.data[0]["title"] == movie.title
        assert len(response.data[0]["genres"]) == 2
        assert "name" in response.data[0]["genres"][0]

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
        assert len(response.data) == 1
        assert response.data[0]["name"] == room.name

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
        assert len(response.data) == 1
        assert response.data[0]["movie"]["title"] == session.movie.title
        assert response.data[0]["room"]["name"] == session.room.name

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