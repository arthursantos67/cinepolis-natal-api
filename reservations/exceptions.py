from rest_framework.exceptions import APIException


class ReservationError(Exception):
    default_code = "RESERVATION_ERROR"
    default_message = "Reservation could not be completed."
    status_code = 400

    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class SeatUnavailableError(ReservationError):
    default_code = "SEAT_UNAVAILABLE"
    default_message = "One or more selected seats are already reserved or purchased."
    status_code = 409


class InvalidSeatSelectionError(ReservationError):
    default_code = "INVALID_SEAT_SELECTION"
    default_message = "One or more selected seats are invalid for this session."
    status_code = 400


class SessionNotFoundError(ReservationError):
    default_code = "SESSION_NOT_FOUND"
    default_message = "Session not found."
    status_code = 404


class SeatAlreadyReservedApiException(APIException):
    status_code = 409
    default_code = "SEAT_ALREADY_RESERVED"
    default_detail = "One or more selected seats are already reserved or purchased."