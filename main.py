import os
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, Redis
from aiogram_dialog import setup_dialogs

from configurations import get_config
from bot import get_all_routers
from bot.middlewares.db_middleware import initialize_database  # ✅ Подключаем мидлвару

current_directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_directory, 'application.log')

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - [%(levelname)s] - %(name)s - "
                           "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
                    filename=log_file_path)

async def run_bot():
    config = get_config()

    # Инициализируем Redis и хранилище для FSM
    redis = Redis(host='localhost')
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = RedisStorage(redis=redis, key_builder=key_builder)

    # Настройки бота
    default = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=config.bot_config.get_token(), default=default)
    dp = Dispatcher(storage=storage)

    dp.include_router(await get_all_routers())

    setup_dialogs(dp)

    # ✅ Теперь инициализируем базу через `initialize_database()`
    await initialize_database()
    logging.info("✅ Таблицы проверены/созданы в базе данных!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
