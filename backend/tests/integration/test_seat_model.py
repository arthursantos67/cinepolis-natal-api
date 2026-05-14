import pytest
from django.core.exceptions import ValidationError

from catalog.models import Room
from reservations.models import Seat, SeatRow


@pytest.mark.django_db
def test_create_seat_row_successfully():
    room = Room.objects.create(name="Room 1", capacity=100)

    row = SeatRow.objects.create(room=room, name="A")

    assert row.id is not None
    assert row.room == room
    assert row.name == "A"


@pytest.mark.django_db
def test_seat_row_name_is_normalized_to_uppercase():
    room = Room.objects.create(name="Room 1", capacity=100)

    row = SeatRow.objects.create(room=room, name="a")

    assert row.name == "A"


@pytest.mark.django_db
def test_seat_row_name_is_trimmed():
    room = Room.objects.create(name="Room 1", capacity=100)

    row = SeatRow.objects.create(room=room, name="  a  ")

    assert row.name == "A"


@pytest.mark.django_db
def test_seat_row_must_be_unique_per_room():
    room = Room.objects.create(name="Room 1", capacity=100)

    SeatRow.objects.create(room=room, name="A")

    with pytest.raises(ValidationError):
        SeatRow.objects.create(room=room, name="a")


@pytest.mark.django_db
def test_same_seat_row_name_can_exist_in_different_rooms():
    room_1 = Room.objects.create(name="Room 1", capacity=100)
    room_2 = Room.objects.create(name="Room 2", capacity=100)

    row_1 = SeatRow.objects.create(room=room_1, name="A")
    row_2 = SeatRow.objects.create(room=room_2, name="A")

    assert row_1.pk != row_2.pk


@pytest.mark.django_db
def test_seat_row_name_cannot_be_blank():
    room = Room.objects.create(name="Room 1", capacity=100)

    with pytest.raises(ValidationError):
        SeatRow.objects.create(room=room, name="   ")


@pytest.mark.django_db
def test_seat_row_name_must_contain_only_letters():
    room = Room.objects.create(name="Room 1", capacity=100)

    with pytest.raises(ValidationError):
        SeatRow.objects.create(room=room, name="A-1")


@pytest.mark.django_db
def test_create_seat_successfully():
    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    seat = Seat.objects.create(row=row, number=1)

    assert seat.id is not None
    assert seat.row == row
    assert seat.number == 1
    assert seat.room == room


@pytest.mark.django_db
def test_seat_number_must_be_unique_per_row():
    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    Seat.objects.create(row=row, number=1)

    with pytest.raises(ValidationError):
        Seat.objects.create(row=row, number=1)


@pytest.mark.django_db
def test_same_seat_number_can_exist_in_different_rows():
    room = Room.objects.create(name="Room 1", capacity=100)
    row_a = SeatRow.objects.create(room=room, name="A")
    row_b = SeatRow.objects.create(room=room, name="B")

    seat_1 = Seat.objects.create(row=row_a, number=1)
    seat_2 = Seat.objects.create(row=row_b, number=1)

    assert seat_1.pk != seat_2.pk


@pytest.mark.django_db
def test_seat_number_must_be_greater_than_zero():
    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    with pytest.raises(ValidationError):
        Seat.objects.create(row=row, number=0)


@pytest.mark.django_db
def test_seat_row_string_representation():
    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")

    assert str(row) == "Room 1 - Row A"


@pytest.mark.django_db
def test_seat_string_representation():
    room = Room.objects.create(name="Room 1", capacity=100)
    row = SeatRow.objects.create(room=room, name="A")
    seat = Seat.objects.create(row=row, number=1)

    assert str(seat) == "Room 1 - A1"