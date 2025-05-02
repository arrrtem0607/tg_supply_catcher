from datetime import datetime, timedelta
from sqlalchemy import inspect, text, select
from sqlalchemy.orm import joinedload
from aiohttp import ClientSession

from database.entities.core import Base, Database
from database.entities.models import User, Client, Supply, Subscription, Tariff
from bot.enums.status_enums import Status
from bot.utils.mpwave_api import MPWAVEAPI
from bot.utils.wildberries_api import WildberriesAPI
from database.controller.balance_controller import BalanceController
from database.db_utils import session_manager
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)

STATUS_TRANSLATION = {
    "RECEIVED": "📥 Получено",
    "CATCHING": "🎯 Ловится",
    "CAUGHT": "✅ Поймано",
    "ERROR": "❌ Ошибка",
    "CANCELLED": "🚫 Отменено",
    "PLANNED": "📌 Запланировано",
    "IN_PROGRESS": "⏳ В процессе",
    "COMPLETED": "✅ Завершено",
}

async def fetch_supplies_from_api(client_id: str):
    """Запрашивает поставки клиента через MPWAVEAPI."""
    return await MPWAVEAPI.fetch_supplies_from_api(client_id)

class ORMController:
    def __init__(self, db: Database = Database()):
        self.db = db
        self.api = MPWAVEAPI()
        self.wb_api = WildberriesAPI()
        self.balance = BalanceController(db)  # ← добавлено
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
    async def add_client(self, session, tg_id: int, client_id: str, name: str, cookies: str):
        # Проверка по составному ключу
        stmt = select(Client).where(Client.client_id == client_id, Client.user_id == tg_id)
        if (await session.execute(stmt)).scalars().first():
            return  # уже существует

        session.add(Client(
            client_id=client_id,
            user_id=tg_id,
            name=name,
            cookies=cookies
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
    async def get_supplies_by_client(self, session, user_id: int, client_id: str):

        result = await session.execute(select(Client).where(Client.client_id == client_id, Client.user_id == user_id))
        client = result.scalars().first()
        if not client:
            return []

        db_supplies = await session.execute(select(Supply).options(joinedload(Supply.client), joinedload(Supply.user)).where(Supply.client_id == client_id))
        db_supplies = {str(s.id): s for s in db_supplies.scalars().all()}

        supplies, api_error = await self.api.fetch_supplies_from_api(client_id)
        if api_error:
            return [s.to_dict() for s in db_supplies.values()]

        api_supply_ids = {str(s.get("supplyId") or s.get("preorderId")) for s in supplies}
        db_supply_ids = set(db_supplies.keys())

        for supply_id in db_supply_ids - api_supply_ids:
            await session.delete(db_supplies[supply_id])

        new_supplies = []
        for supply in supplies:
            supply_id = str(supply.get("supplyId") or supply.get("preorderId"))
            api_created_at = supply.get("createDate")
            if api_created_at:
                api_created_at = datetime.fromisoformat(api_created_at).replace(tzinfo=None)

            warehouse_name = supply.get("warehouseName", "❌ Неизвестный склад")
            warehouse_address = supply.get("warehouseAddress", "❌ Неизвестный адрес")
            box_type = supply.get("boxTypeName", "❌ Неизвестный тип")

            if supply_id not in db_supply_ids:
                new_supplies.append(Supply(id=int(supply_id), user_id=user_id, client_id=client_id, status=Status.RECEIVED.value, api_created_at=api_created_at, warehouse_name=warehouse_name, warehouse_address=warehouse_address, box_type=box_type))
            else:
                existing = db_supplies[supply_id]
                if not existing.api_created_at and api_created_at:
                    existing.api_created_at = api_created_at
                existing.warehouse_name = warehouse_name
                existing.warehouse_address = warehouse_address
                existing.box_type = box_type

        session.add_all(new_supplies)
        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "client_id": str(s.client_id),
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "api_created_at": s.api_created_at.isoformat() if s.api_created_at else None,
                "warehouse_name": s.warehouse_name,
                "warehouse_address": s.warehouse_address,
                "box_type": s.box_type,
                "client_name": s.client.name if s.client else None,
                "user_name": s.user.username if s.user else None,
            }
            for s in list(db_supplies.values()) + new_supplies
        ]

    @session_manager
    async def register_user(self, session, tg_id: int, username: str | None):
        from sqlalchemy import select  # если не импортировано выше
        logger.debug(f"📍 Попытка регистрации пользователя: tg_id={tg_id}, username={username}")

        try:
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalars().first()
            if user:
                logger.debug(f"⚠️ Пользователь с tg_id={tg_id} уже существует")
                return {"message": "Пользователь уже зарегистрирован"}

            logger.debug(f"🔄 Вызов API для регистрации пользователя tg_id={tg_id}")
            response = await self.api.register_user_api(tg_id)

            if response is None:
                logger.error("❌ Ошибка: не удалось получить ответ от API (None)")
                return {"error": "Ошибка подключения к API"}

            if response.status != 200:
                error_text = await response.text()
                logger.error(f"❌ Ошибка регистрации через API: {response.status} | {error_text}")
                return {"error": f"Ошибка регистрации: {error_text}"}

            new_user = User(tg_id=tg_id, username=username or "unknown")
            session.add(new_user)

            logger.debug(f"✅ Пользователь tg_id={tg_id} успешно зарегистрирован в базе")
            return {"message": "Пользователь зарегистрирован в системе"}

        except Exception as e:
            logger.error(f"❌ Исключение в register_user: {e}", exc_info=True)
            return {"error": "Внутренняя ошибка при регистрации пользователя"}

    @session_manager
    async def register_client(self, session, tg_id: int, client_id: str, name: str, cookies: str):
        existing_client = await self.get_client_by_name(tg_id, name)
        if existing_client:
            return {"error": "Кабинет уже зарегистрирован"}

        async with ClientSession() as http_session:
            is_valid = await self.wb_api.validate_token(token="", cookie_string=cookies, session=http_session)
            if not is_valid:
                return {"error": "Невалидные cookies. Проверьте и попробуйте снова."}

        api_result = await self.api.register_client_api(tg_id, client_id, name, cookies)
        if "error" in api_result:
            return {"error": api_result["error"]}

        await self.add_client(tg_id, client_id, name, cookies)
        return {"message": "Кабинет зарегистрирован", "client_id": client_id}

    @session_manager
    async def confirm_supply_catching(
            self, session, supply_id: int, start_date: str, end_date: str, skip_dates: list, coefficient: float
    ):
        """Сначала отправляет задачу на отлов на сервер, затем обновляет поставку в БД при успехе."""

        result = await session.execute(select(Supply).where(Supply.id == int(supply_id)))
        supply = result.scalars().first()

        if not supply:
            logger.warning(f"⚠️ Поставка с ID {supply_id} не найдена!")
            return {"error": f"Поставка с ID {supply_id} не найдена!"}

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            skip_dt_list = [datetime.fromisoformat(d) for d in skip_dates]
        except ValueError as e:
            logger.error(f"❌ Ошибка при преобразовании дат: {e}")
            return {"error": f"Ошибка при обработке дат: {e}"}

        # ⬇️ Подготовка данных для API
        api_data = {
            "client_id": str(supply.client_id),
            "preorder_id": supply.id,
            "start_date": start_date,
            "end_date": end_date,
            "skip_dates": skip_dates,
            "coefficient": coefficient,
        }

        # ⬇️ Отправка задачи на отлов
        response = await self.api.start_task_api(api_data)

        if not response or response.status != 200:
            text = await response.text() if response else "нет ответа от сервера"
            logger.error(f"❌ Ошибка при запуске отлова на сервере: {text}")
            return {"error": f"Ошибка при запуске отлова: {text}"}

        # ⬇️ Только если сервер принял — обновляем запись в БД
        supply.status = Status.CATCHING.value
        supply.start_catch_date = start_dt
        supply.end_catch_date = end_dt
        supply.skip_dates = skip_dt_list
        supply.coefficient = coefficient

        logger.info(
            f"✅ Поставка {supply_id} обновлена и отправлена на отлов: "
            f"start_catch_date={start_dt}, end_catch_date={end_dt}, "
            f"skip_dates={skip_dt_list}, coefficient={coefficient}"
        )

        return {"message": f"Поставка {supply_id} обновлена и отправлена на отлов"}

    @session_manager
    async def get_supply_by_id(self, session, supply_id: str):
        """Получаем поставку по ID"""
        result = await session.execute(select(Supply).where(Supply.id == int(supply_id)))
        return result.scalars().first()  # Возвращаем первую найденную поставку (или None, если не найдена)

    @session_manager
    async def cancel_catching(self, session, client_id: str, supply_id: int):
        """Отменяет отлов поставки через MPWAVEAPI и обновляет статус в БД."""
        logger.info(f"🚫 Отмена отлова поставки {supply_id} для клиента {client_id}")

        response = await self.api.cancel_task_api(client_id, supply_id)
        if response.status != 200:
            error_text = await response.text()
            logger.error(f"❌ Ошибка API отмены отлова: {error_text}")
            return {"error": f"Ошибка API: {error_text}"}

        result = await session.execute(select(Supply).where(Supply.id == supply_id))
        supply = result.scalars().first()
        if not supply:
            logger.warning(f"⚠️ Поставка {supply_id} не найдена в БД")
            return {"error": "Поставка не найдена в базе"}

        supply.status = Status.RECEIVED.value
        logger.info(f"✅ Статус поставки {supply_id} обновлен на RECEIVED")
        return {"message": f"Поставка {supply_id} успешно отменена"}

    @session_manager
    async def update_client_name(self, session, client_id: str, new_name: str):
        logger.info(f"🔄 Обновление имени клиента {client_id} на '{new_name}'")

        # Сначала пытаемся обновить на сервере
        response = await self.api.update_client_name_api(client_id, new_name)
        if response is None or response.status != 200:
            error_text = await response.text() if response else "Нет ответа"
            logger.error(f"❌ Ошибка при обновлении имени клиента на сервере: {error_text}")
            return {"error": f"Ошибка при обновлении имени на сервере: {error_text}"}

        # Если успех — обновляем в БД
        result = await session.execute(select(Client).where(Client.client_id == client_id))
        client = result.scalars().first()

        if not client:
            logger.warning(f"⚠️ Клиент {client_id} не найден в БД")
            return {"error": "Клиент не найден в базе"}

        client.name = new_name
        logger.info(f"✅ Имя клиента {client_id} обновлено в БД на '{new_name}'")
        return {"message": "Имя клиента обновлено"}

    @session_manager
    async def update_client_cookies(self, session, client_id: str, new_cookies: str):
        logger.info(f"🔄 Запрос на обновление cookies клиента {client_id}")

        # Сначала проверяем валидность cookies
        async with ClientSession() as http_session:
            is_valid = await self.wb_api.validate_token(token="", cookie_string=new_cookies, session=http_session)
            if not is_valid:
                logger.warning(f"❌ Переданные cookies невалидны для клиента {client_id}")
                return {"error": "Невалидные cookies. Проверьте и попробуйте снова."}

        # Отправляем обновление на сервер
        response = await self.api.update_client_cookies_api(client_id, new_cookies)
        if response is None or response.status != 200:
            error_text = await response.text() if response else "Нет ответа"
            logger.error(f"❌ Ошибка при обновлении cookies клиента на сервере: {error_text}")
            return {"error": f"Ошибка при обновлении cookies на сервере: {error_text}"}

        # Обновляем в базе данных
        result = await session.execute(select(Client).where(Client.client_id == client_id))
        client = result.scalars().first()

        if not client:
            logger.warning(f"⚠️ Клиент {client_id} не найден в БД")
            return {"error": "Клиент не найден в базе"}

        client.cookies = new_cookies
        logger.info(f"✅ Cookies клиента {client_id} успешно обновлены в БД")
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
            # Продлеваем подписку: добавляем 30 дней от текущей даты окончания
            current_subscription.end_date += timedelta(days=30)
            logger.info(f"🔁 Продлена подписка для user_id={user_id} до {current_subscription.end_date}")
            return current_subscription.end_date
        else:
            # Создаём новую подписку
            new_subscription = Subscription(
                user_id=user_id,
                tariff_id=tariff_id,
                start_date=start,
                end_date=end,
                is_active=True,
            )
            session.add(new_subscription)
            logger.info(f"🆕 Создана новая подписка для user_id={user_id}")
            return new_subscription.end_date

    @session_manager
    async def get_active_subscription(self, session, user_id: int):
        stmt = (
            select(Subscription)
            .options(joinedload(Subscription.tariff))  # подгружаем tariff сразу
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
