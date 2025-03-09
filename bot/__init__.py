from aiogram import Router
from aiogram_dialog import setup_dialogs

from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.middlewares.is_admin_middleware import IsAdminMiddleware  # Импорт новой миддлвари
from bot.handlers.handlers import router as start_router
from bot.dialogs.main_menu_dialog import main_menu_dialog# Импортируем сам диалог
from bot.dialogs.info_dialog import info_dialog
from bot.dialogs.price_dialog import price_dialog
from bot.dialogs.add_client_dialog import add_client_dialog
from bot.dialogs.task_dialog import task_dialog
from database.entities.core import Database
from configurations import get_config

config = get_config()

async def get_all_routers():
    # Создаем экземпляры миддлваров
    db: Database = Database()
    db_session_middleware = DbSessionMiddleware(db.async_session_factory)

    # Получаем список ID администраторов
    admin_middleware = IsAdminMiddleware()

    # Подключаем миддлвары к start_router (обычные функции)
    start_router.message.middleware(db_session_middleware)
    start_router.callback_query.middleware(db_session_middleware)

    router: Router = Router()

    router.include_router(start_router)
    router.include_router(main_menu_dialog)
    router.include_router(price_dialog)
    router.include_router(info_dialog)
    router.include_router(add_client_dialog)
    router.include_router(task_dialog)

    setup_dialogs(router)

    return router
