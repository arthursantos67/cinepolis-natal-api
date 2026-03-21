from django.core.cache import cache


class SeatLockManager:
    def __init__(self, timeout_seconds: int = 600):
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def build_key(session_id, seat_id) -> str:
        return f"lock:session-seat:{session_id}:{seat_id}"

    def acquire(self, session_id, seat_id, owner_id: str) -> bool:
        key = self.build_key(session_id, seat_id)
        return cache.add(key, str(owner_id), timeout=self.timeout_seconds)

    def release(self, session_id, seat_id) -> None:
        key = self.build_key(session_id, seat_id)
        cache.delete(key)