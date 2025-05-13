import asyncio
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, Redis
from aiogram_dialog import setup_dialogs

from configurations import get_config
from bot import get_all_routers
from services.payments.service import router as webhook_router
from services.utils.logger import setup_logger
from bot.middlewares.db_middleware import initialize_database
from services.payments.client import TochkaAPIClient
from configurations.payments_config import PaymentsConfig

logger = setup_logger(__name__)

# -- Lifespan для FastAPI --
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(5)  # ⏱️ дать FastAPI полностью подняться
    client = TochkaAPIClient(PaymentsConfig())
    try:
        url = "https://82ef-45-144-233-139.ngrok-free.app/webhook/tochka/"  # Заменить на актуальный
        await client.setup_webhook(url)
        logger.info("✅ Вебхук Точки успешно зарегистрирован")
    except Exception as e:
        logger.error("❌ Ошибка при регистрации вебхука Точки: %s", e)

    yield  # ⏳ Запуск приложения

    try:
        await client.delete_webhook()
        logger.info("🗑️ Вебхук Точки удалён при завершении работы")
    except Exception as e:
        logger.error("❌ Не удалось удалить вебхук Точки: %s", e)

# -- FastAPI app --
app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)


async def run_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8010, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start the bot / Запустить бота"),
        BotCommand(command="/menu", description="Main menu / Главное меню"),
        BotCommand(command="/language", description="Change language / Сменить язык"),
        BotCommand(command="/drop_tables", description="⚠️ Удалить все таблицы (dev only)"),
        BotCommand(command="/truncate_tables", description="🧹 Очистить все таблицы (dev only)"),
    ]
    await bot.set_my_commands(commands)


async def run_bot():
    config = get_config()

    redis = Redis(host="localhost")
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = RedisStorage(redis=redis, key_builder=key_builder)

    bot = Bot(
        token=config.bot_config.get_token(),
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher(storage=storage)

    dp.include_router(await get_all_routers())
    setup_dialogs(dp)

    await setup_bot_commands(bot)
    await initialize_database()
    logger.info("✅ Таблицы проверены/созданы в базе данных!")
    logger.info("✅ Бот успешно запущен")

    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        run_fastapi(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
