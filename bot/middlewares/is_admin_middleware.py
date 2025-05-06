from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from configurations import get_config
from services.utils.logger import setup_logger

# Настройка логгера
logger = setup_logger(__name__)
config = get_config()


class IsAdminMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.admin_ids = config.bot_config.get_developers_id()
        logger.info("IsAdminMiddleware инициализирована")

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
            if str(user_id) in self.admin_ids:
                logger.info(f"Пользователь с ID {user_id} является администратором")
                return await handler(event, data)
            else:
                logger.warning(f"Доступ запрещен для пользователя с ID {user_id}")
                await event.answer("У вас нет прав для выполнения этой команды.")
        else:
            # Игнорируем не Message события и передаем их дальше без обработки
            logger.debug("IsAdminMiddleware игнорирует не Message событие")
            return await handler(event, data)
