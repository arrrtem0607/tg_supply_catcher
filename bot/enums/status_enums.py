from enum import Enum


class Status(str, Enum):
    """Перечисление статусов процесса с методами перевода."""

    RECEIVED = "received"
    CATCHING = "catching"
    CAUGHT = "caught"
    ERROR = "error"
    CANCELLED = "cancelled"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    def get_translation(self) -> str:
        """Переводит статус на русский язык."""
        translations = {
            Status.RECEIVED: "📥 Получено",
            Status.CATCHING: "🎯 Ловится",
            Status.CAUGHT: "✅ Поймано",
            Status.ERROR: "❌ Ошибка",
            Status.CANCELLED: "🚫 Отменено",
            Status.PLANNED: "📌 Запланировано",
            Status.IN_PROGRESS: "⏳ В процессе",
            Status.COMPLETED: "✅ Завершено",
        }
        return translations.get(self, "❌ Неизвестный статус")

    @classmethod
    def from_str(cls, value: str) -> "Status | None":
        """Преобразует строку в объект `Status`, если возможно."""
        try:
            return cls(value.lower())
        except ValueError:
            return None  # Если статус не найден, возвращаем None
