import logging
from sqlalchemy import inspect, text, select
import aiohttp

from database.entities.core import Base, Database
from database.entities.models import User
from database.entities.models import Client
from datetime import datetime, timezone


logger = logging.getLogger(__name__)

def session_manager(func):
    """Декоратор для автоматического управления сессией"""
    async def wrapper(self, *args, **kwargs):
        async with self.db.session() as session:  # ✅ Открываем сессию
            async with session.begin():  # ✅ Начинаем транзакцию
                try:
                    result = await func(self, session, *args, **kwargs)  # ✅ Передаем session правильно
                    await session.commit()  # ✅ Коммитим изменения
                    logger.debug(f"✅ {func.__name__} выполнена успешно")
                    return result
                except Exception as e:
                    await session.rollback()  # ✅ Откатываем при ошибке
                    logger.error(f"❌ Ошибка в {func.__name__}: {e}", exc_info=True)
                    raise e
    return wrapper

class ORMController:
    BASE_URL = "https://goapimpwave.ru"  # Базовый URL API
    def __init__(self, db: Database = Database()):
        self.db = db
        logger.info("ORMController initialized")

    async def create_tables(self):
        async with self.db.async_engine.begin() as conn:

            def sync_inspect(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()

            logger.info(f"🔍 Используемая база данных: {self.db.async_engine.url.database}")

            # ✅ Устанавливаем схему `public`
            await conn.run_sync(lambda c: c.execute(text("SET search_path TO public")))

            existing_tables = await conn.run_sync(sync_inspect)
            logger.info(f"📌 Существующие таблицы: {existing_tables}")

            found_metadata_tables = list(Base.metadata.tables.keys())
            logger.info(f"📂 Найденные таблицы в metadata: {found_metadata_tables}")

            # Если есть существующие таблицы, но они не совпадают с метаданными
            if existing_tables and set(existing_tables) != set(found_metadata_tables):
                logger.warning("⚠️ Обнаружены изменения в моделях! Пересоздаем таблицы...")

                # ✅ Удаляем все таблицы
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("🗑️ Все таблицы удалены!")

                # ✅ Создаем их заново
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Таблицы успешно пересозданы!")

            elif not existing_tables:
                logger.info("🔧 Таблицы отсутствуют, создаем их...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Таблицы успешно созданы!")
            else:
                logger.info("✅ Структура БД актуальна, изменений не требуется.")

    @session_manager
    async def add_user(self, session, tg_id: int, username: str | None):
        """Добавляет нового пользователя в базу данных, если его еще нет"""
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

        if not user:
            new_user = User(
                tg_id=tg_id,
                username=username if username else "unknown",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            session.add(new_user)
            logger.info(f"✅ Добавлен новый пользователь: {tg_id} ({new_user.username})")
        else:
            logger.info(f"ℹ️ Пользователь {tg_id} уже существует")

    @session_manager
    async def add_client(self, session, tg_id: int, name: str, cookies: str):
        """Добавление нового кабинета в базу данных"""
        result = await session.execute(select(Client).where(Client.name == name))
        existing_client = result.scalars().first()

        if existing_client:
            logger.info(f"⚠️ Кабинет с client_id {name} уже существует!")
            return

        new_client = Client(
            name=name,
            user_id=tg_id,
            cookies=cookies,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)  # ✅ Убираем `tzinfo`
        )

        session.add(new_client)
        logger.info(f"✅ Кабинет {name} успешно добавлен для пользователя {tg_id}")

    @session_manager
    async def get_client_by_name(self, session, tg_id: int, name: str):
        """Проверяем, существует ли кабинет с таким именем у пользователя"""
        result = await session.execute(
            select(Client).where(Client.name == name, Client.user_id == tg_id)
        )
        return result.scalars().first()

    @session_manager
    async def get_clients_by_user_id(self, session, tg_id: int):
        """Получение списка всех кабинетов пользователя"""
        result = await session.execute(
            select(Client).where(Client.user_id == tg_id)
        )
        clients = result.scalars().all()

        logger.info(f"📋 Найдено {len(clients)} кабинетов для пользователя {tg_id}")
        return clients

    @session_manager
    async def get_supplies_by_client(self, session, user_id: int, client_id: int):
        """Получить список поставок для указанного клиента (client_id), принадлежащего user_id"""

        # Проверяем, принадлежит ли клиент пользователю
        result = await session.execute(
            select(Client).where(Client.client_id == client_id, Client.user_id == user_id)
        )
        client = result.scalars().first()

        if not client:
            logger.warning(f"⚠️ Пользователь {user_id} пытался получить поставки не своего клиента ({client_id})!")
            return []

        # Запрос к API
        url = f"{self.BASE_URL}/catcher/all_supplies"
        params = {"client_id": client_id}

        async with aiohttp.ClientSession() as http_session:
            try:
                async with http_session.get(url, params=params) as response:
                    if response.status == 200:
                        supplies = await response.json()

                        # 🔥 Логируем JSON для анализа
                        logger.info(f"📦 JSON ответа API: {supplies}")

                        return supplies
                    else:
                        logger.error(f"❌ Ошибка запроса поставок: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"❌ Ошибка при получении поставок: {e}", exc_info=True)
                return []
