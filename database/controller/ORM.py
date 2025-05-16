from datetime import datetime, timedelta
from sqlalchemy import inspect, text, select
from sqlalchemy.orm import joinedload
from aiohttp import ClientSession

from database.entities.core import Base, Database
from database.entities.models import User, Client, Subscription, Tariff
from services.utils.mpwave_api import MPWAVEAPI
from services.utils.wildberries_api import WildberriesAPI
from database.controller.balance_controller import BalanceController
from database.controller.supply_controller import SupplyController
from database.db_utils import session_manager
from services.utils.logger import setup_logger

logger = setup_logger(__name__, level="WARNING")

class ORMController:
    def __init__(self, db: Database = Database()):
        self.db = db
        self.api = MPWAVEAPI()
        self.wb_api = WildberriesAPI()
        self.balance = BalanceController(db)
        self.supply = SupplyController(db)
        logger.info("ORMController initialized")

    async def create_tables(self):
        async with self.db.async_engine.begin() as conn:

            def sync_inspect(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()

            logger.info(f"🔍 Используемая база данных: {self.db.async_engine.url.database}")
            await conn.run_sync(lambda c: c.execute(text("SET search_path TO public")))

            existing_tables = await conn.run_sync(sync_inspect)
            logger.info(f"📌 Существующие таблицы: {existing_tables}")

            found_metadata_tables = [
                name.split(".")[-1]
                for name in Base.metadata.tables.keys()
            ]
            logger.info(f"📂 Найденные таблицы в metadata: {found_metadata_tables}")

            if existing_tables and set(existing_tables) != set(found_metadata_tables):
                logger.warning("⚠️ Обнаружены изменения в моделях! Пересоздаем таблицы...")

                await conn.run_sync(Base.metadata.drop_all)
                logger.info("🗑️ Все таблицы удалены!")

                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Таблицы успешно пересозданы!")

            elif not existing_tables:
                logger.info("🔧 Таблицы отсутствуют, создаем их...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Таблицы успешно созданы!")
            else:
                logger.info("✅ Структура БД актуальна, изменений не требуется.")

    async def drop_tables(self):
        async with self.db.async_engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute(text("SET search_path TO public")))
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("🗑️ Все таблицы удалены вручную!")

    async def truncate_tables(self):
        async with self.db.async_engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute(text("SET search_path TO public")))
            tables = Base.metadata.sorted_tables
            for table in tables:
                await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
            logger.info("🧹 Все таблицы очищены (TRUNCATE).")

    @session_manager
    async def seed_tariffs(self, session):
        existing = await session.execute(select(Tariff))
        if existing.scalars().first():
            logger.info("📦 Тарифы уже существуют — пропускаем инициализацию.")
            return

        tariffs = [
            Tariff(name="Месячная подписка", price=25000, duration_days=30, is_subscription=True),
            Tariff(name="Разовый отлов (короб)", price=1000, duration_days=None, is_subscription=False),
            Tariff(name="Разовый отлов (паллет)", price=1500, duration_days=None, is_subscription=False),
        ]
        session.add_all(tariffs)
        logger.info("✅ Добавлены стартовые тарифы")

    @session_manager
    async def add_client(self, session, tg_id: int, client_id: str, name: str, cookies: str, refresh_token: str):
        stmt = select(Client).where(Client.client_id == client_id, Client.user_id == tg_id)
        if (await session.execute(stmt)).scalars().first():
            return
        session.add(Client(
            client_id=client_id,
            user_id=tg_id,
            name=name,
            cookies=cookies,
            refresh_token=refresh_token
        ))

    @session_manager
    async def get_client_by_name(self, session, tg_id: int, name: str):
        result = await session.execute(select(Client).where(Client.name == name, Client.user_id == tg_id))
        return result.scalars().first()

    @session_manager
    async def get_clients_by_user_id(self, session, tg_id: int):
        result = await session.execute(select(Client).where(Client.user_id == tg_id))
        return result.scalars().all()

    @session_manager
    async def register_user(self, session, tg_id: int, username: str | None):
        logger.debug(f"📍 Попытка регистрации пользователя: tg_id={tg_id}, username={username}")

        try:
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalars().first()
            if user:
                logger.debug(f"⚠️ Пользователь с tg_id={tg_id} уже существует")
                return {"message": "Пользователь уже зарегистрирован"}

            response = await self.api.register_user_api(tg_id)
            if response is None or response.status != 200:
                error_text = await response.text() if response else "Нет ответа от API"
                logger.error(f"❌ Ошибка регистрации через API: {error_text}")
                return {"error": f"Ошибка регистрации: {error_text}"}

            session.add(User(tg_id=tg_id, username=username or "unknown"))
            return {"message": "Пользователь зарегистрирован в системе"}

        except Exception as e:
            logger.error(f"❌ Исключение в register_user: {e}", exc_info=True)
            return {"error": "Внутренняя ошибка при регистрации пользователя"}

    @session_manager
    async def register_client(self, session, tg_id: int, client_id: str, name: str, cookies: str, refresh_token: str):
        existing_client = await self.get_client_by_name(tg_id, name)
        if existing_client:
            return {"error": "Кабинет уже зарегистрирован"}

        async with ClientSession() as http_session:
            is_valid = await self.wb_api.validate_token(token="", cookie_string=cookies, session=http_session)
            if not is_valid:
                return {"error": "Невалидные cookies. Проверьте и попробуйте снова."}

        api_result = await self.api.register_client_api(tg_id, client_id, name, cookies, refresh_token)
        if "error" in api_result:
            return {"error": api_result["error"]}

        await self.add_client(tg_id, client_id, name, cookies, refresh_token)
        return {"message": "Кабинет зарегистрирован", "client_id": client_id}

    @session_manager
    async def update_client_name(self, session, client_id: str, new_name: str):
        response = await self.api.update_client_name_api(client_id, new_name)
        if response is None or response.status != 200:
            error_text = await response.text() if response else "Нет ответа"
            return {"error": f"Ошибка при обновлении имени на сервере: {error_text}"}

        result = await session.execute(select(Client).where(Client.client_id == client_id))
        client = result.scalars().first()
        if not client:
            return {"error": "Клиент не найден в базе"}

        client.name = new_name
        return {"message": "Имя клиента обновлено"}

    @session_manager
    async def update_client_cookies(self, session, client_id: str, new_cookies: str):
        async with ClientSession() as http_session:
            is_valid = await self.wb_api.validate_token(token="", cookie_string=new_cookies, session=http_session)
            if not is_valid:
                return {"error": "Невалидные cookies. Проверьте и попробуйте снова."}

        response = await self.api.update_client_cookies_api(client_id, new_cookies)
        if response is None or response.status != 200:
            error_text = await response.text() if response else "Нет ответа"
            return {"error": f"Ошибка при обновлении cookies на сервере: {error_text}"}

        result = await session.execute(select(Client).where(Client.client_id == client_id))
        client = result.scalars().first()
        if not client:
            return {"error": "Клиент не найден в базе"}

        client.cookies = new_cookies
        return {"message": "Cookies клиента обновлены"}

    @session_manager
    async def create_subscription(self, session, user_id: int, tariff_id: int, start: datetime, end: datetime):
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.is_active == True)
            .limit(1)
        )
        result = await session.execute(stmt)
        current_subscription = result.scalars().first()

        if current_subscription:
            current_subscription.end_date += timedelta(days=30)
            return current_subscription.end_date
        else:
            new_subscription = Subscription(
                user_id=user_id,
                tariff_id=tariff_id,
                start_date=start,
                end_date=end,
                is_active=True,
            )
            session.add(new_subscription)
            return new_subscription.end_date

    @session_manager
    async def get_active_subscription(self, session, user_id: int):
        stmt = (
            select(Subscription)
            .options(joinedload(Subscription.tariff))
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @session_manager
    async def get_all_tariffs(self, session):
        result = await session.execute(select(Tariff))
        return result.scalars().all()
