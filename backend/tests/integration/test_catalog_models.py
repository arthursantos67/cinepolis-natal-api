import pytest
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from catalog.models import Genre, Movie, Room, Session


@pytest.mark.django_db
class TestCatalogModels:

    def test_create_genre_successfully(self):
        genre = Genre.objects.create(name="Action")

        assert genre.id is not None
        assert genre.name == "Action"

    def test_genre_name_must_be_unique(self):
        Genre.objects.create(name="Action")

        with pytest.raises(IntegrityError):
            Genre.objects.create(name="Action")

    def test_create_movie_with_genres(self):
        genre1 = Genre.objects.create(name="Action")
        genre2 = Genre.objects.create(name="Sci-Fi")

        movie = Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )

        movie.genres.set([genre1, genre2])

        assert movie.id is not None
        assert movie.genres.count() == 2

    def test_movie_unique_title_and_release_date(self):
        Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )

        with pytest.raises(IntegrityError):
            Movie.objects.create(
                title="Interstellar",
                synopsis="Another synopsis",
                duration_minutes=170,
                release_date="2014-11-07",
                poster_url="https://example.com/poster2.jpg",
            )

    def test_create_room_successfully(self):
        room = Room.objects.create(name="Room 1", capacity=100)

        assert room.id is not None
        assert room.capacity == 100

    def test_room_capacity_must_be_positive(self):
        room = Room(
            name="Room 1",
            capacity=0,
        )

        with pytest.raises(ValidationError):
            room.full_clean()

    def test_create_valid_session(self):
        genre = Genre.objects.create(name="Action")

        movie = Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )
        movie.genres.add(genre)

        room = Room.objects.create(name="Room 1", capacity=100)

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=120)

        session = Session.objects.create(
            movie=movie,
            room=room,
            start_time=start_time,
            end_time=end_time,
        )

        assert session.id is not None

    def test_session_end_time_must_be_after_start_time(self):
        genre = Genre.objects.create(name="Action")

        movie = Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )
        movie.genres.add(genre)

        room = Room.objects.create(name="Room 1", capacity=100)

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time - timedelta(minutes=10)

        session = Session(
            movie=movie,
            room=room,
            start_time=start_time,
            end_time=end_time,
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_session_cannot_overlap_in_same_room(self):
        genre = Genre.objects.create(name="Action")

        movie = Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )
        movie.genres.add(genre)

        room = Room.objects.create(name="Room 1", capacity=100)

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=120)

        Session.objects.create(
            movie=movie,
            room=room,
            start_time=start_time,
            end_time=end_time,
        )

        overlapping_start = start_time + timedelta(minutes=30)
        overlapping_end = overlapping_start + timedelta(minutes=120)

        session = Session(
            movie=movie,
            room=room,
            start_time=overlapping_start,
            end_time=overlapping_end,
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_session_can_overlap_in_different_rooms(self):
        genre = Genre.objects.create(name="Action")

        movie = Movie.objects.create(
            title="Interstellar",
            synopsis="Space exploration",
            duration_minutes=169,
            release_date="2014-11-07",
            poster_url="https://example.com/poster.jpg",
        )
        movie.genres.add(genre)

        room1 = Room.objects.create(name="Room 1", capacity=100)
        room2 = Room.objects.create(name="Room 2", capacity=100)

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=120)

        Session.objects.create(
            movie=movie,
            room=room1,
            start_time=start_time,
            end_time=end_time,
        )

        session = Session.objects.create(
            movie=movie,
            room=room2,
            start_time=start_time,
            end_time=end_time,
        )

        assert session.id is not None