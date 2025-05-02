import asyncio
import uvicorn

from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, Redis
from aiogram_dialog import setup_dialogs

from configurations import get_config
from bot import get_all_routers
from payments.service import router as webhook_router
from bot.utils.logger import setup_logger
from bot.middlewares.db_middleware import initialize_database

app = FastAPI()
app.include_router(webhook_router)
logger = setup_logger(__name__)


async def run_fastapi():
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


async def run_bot():
    config = get_config()

    redis = Redis(host='localhost')
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = RedisStorage(redis=redis, key_builder=key_builder)

    bot = Bot(token=config.bot_config.get_token(), default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    dp.include_router(await get_all_routers())
    setup_dialogs(dp)

    # ✅ Теперь инициализируем базу через `initialize_database()`
    await initialize_database()
    logger.info("✅ Таблицы проверены/созданы в базе данных!")

    logger.info("✅ Бот успешно запущен")
    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        run_fastapi(),
        run_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())
