from enum import Enum


class Status(str, Enum):
    """Перечисление статусов процесса."""

    RECEIVED = "received"
    CATCHING = "catching"
    CAUGHT = "caught"
    ERROR = "error"
    CANCELLED = "cancelled"

    @staticmethod
    def list():
        """Возвращает список всех доступных статусов."""
        return [status.value for status in Status]
