import logging
from sqlalchemy import inspect, text, select
from sqlalchemy.orm import joinedload
import aiohttp
import uuid
from datetime import datetime

from database.entities.core import Base, Database
from database.entities.models import User, Client, Supply
from bot.enums.status_enums import Status

logger = logging.getLogger(__name__)

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

async def fetch_supplies_from_api(base_url: str, client_uuid: uuid.UUID):
    """Выполняет запрос к API и возвращает JSON с поставками."""
    url = f"{base_url}/catcher/all_supplies"
    params = {"client_id": str(client_uuid)}

    async with aiohttp.ClientSession() as http_session:
        try:
            async with http_session.get(url, params=params) as response:
                response_text = await response.text()
                if response.status != 200:
                    return None, f"Ошибка API: {response.status}, Ответ: {response_text}"
                return await response.json(), None
        except Exception as e:
            return None, f"Ошибка запроса к API: {e}"

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
    BASE_URL = "http://127.0.0.1:8001"  # Локальный API
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
    async def add_client(self, session, tg_id: int, client_id: str | None, name: str, cookies: str):
        """Добавление нового кабинета в базу данных"""

        # Если client_id не передан, генерируем новый UUID
        if client_id is None:
            client_uuid = uuid.uuid4()
        else:
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                logger.error(f"❌ Некорректный client_id: {client_id}")
                return

        result = await session.execute(select(Client).where(Client.client_id == str(client_uuid)))
        existing_client = result.scalars().first()

        if existing_client:
            logger.info(f"⚠️ Кабинет с client_id {client_uuid} уже существует!")
            return

        new_client = Client(
            client_id=client_uuid,  # ✅ Преобразуем UUID в строку перед сохранением
            name=name,
            user_id=tg_id,
            cookies=cookies
        )

        session.add(new_client)
        logger.info(f"✅ Кабинет {name} (client_id: {client_uuid}) успешно добавлен для пользователя {tg_id}")

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
    async def get_supplies_by_client(self, session, user_id: int, client_id: str):
        """Синхронизация поставок клиента с API и обновление БД"""

        logger.info(f"📌 Начало синхронизации поставок: user_id={user_id}, client_id={client_id}")

        try:
            client_uuid = uuid.UUID(client_id)
        except ValueError:
            logger.error(f"❌ Некорректный client_id: {client_id}")
            return []

        result = await session.execute(
            select(Client).where(Client.client_id == client_uuid, Client.user_id == user_id)
        )
        client = result.scalars().first()

        if not client:
            logger.warning(f"⚠️ Пользователь {user_id} пытался получить поставки не своего клиента ({client_id})!")
            return []

        # ✅ Загружаем все поставки клиента из БД
        db_supplies = await session.execute(
            select(Supply)
            .options(joinedload(Supply.client), joinedload(Supply.user))
            .where(Supply.client_id == client_uuid)
        )
        db_supplies = {str(s.id): s for s in db_supplies.scalars().all()}

        # ✅ Загружаем поставки из API
        supplies, api_error = await fetch_supplies_from_api(self.BASE_URL, client_uuid)

        if api_error:
            logger.error(api_error)
            return [s.to_dict() for s in db_supplies.values()]

        logger.info(f"📦 JSON ответа API: {supplies}")

        # ✅ Получаем ID поставок из API и БД
        api_supply_ids = {str(s.get("supplyId") or s.get("preorderId")) for s in supplies}
        db_supply_ids = set(db_supplies.keys())

        # ✅ Удаляем из БД поставки, которых нет в API
        for supply_id in db_supply_ids - api_supply_ids:
            await session.delete(db_supplies[supply_id])
            logger.info(f"🗑️ Удалена поставка: {supply_id}")

        new_supplies = []
        for supply in supplies:
            supply_id = str(supply.get("supplyId") or supply.get("preorderId"))

            api_created_at = supply.get("createDate")
            if api_created_at:
                api_created_at = datetime.fromisoformat(api_created_at).replace(tzinfo=None)

            # ✅ Новые данные из API
            warehouse_name = supply.get("warehouseName", "❌ Неизвестный склад")
            warehouse_address = supply.get("warehouseAddress", "❌ Неизвестный адрес")
            box_type = supply.get("boxTypeName", "❌ Неизвестный тип")

            if supply_id not in db_supply_ids:
                # ✅ Если поставка новая, ставим ей статус RECEIVED
                new_supplies.append(
                    Supply(
                        id=int(supply_id),
                        user_id=user_id,
                        client_id=client_uuid,
                        status=Status.RECEIVED.value,  # Всегда новый статус "RECEIVED"
                        api_created_at=api_created_at,
                        warehouse_name=warehouse_name,
                        warehouse_address=warehouse_address,
                        box_type=box_type,
                    )
                )
                logger.info(f"➕ Добавлена новая поставка {supply_id} со статусом RECEIVED")
            else:
                # ✅ Если поставка уже есть, просто обновляем данные (но не статус)
                existing_supply = db_supplies[supply_id]
                if not existing_supply.api_created_at and api_created_at:
                    existing_supply.api_created_at = api_created_at
                existing_supply.warehouse_name = warehouse_name
                existing_supply.warehouse_address = warehouse_address
                existing_supply.box_type = box_type
                logger.info(f"🔄 Обновлена информация о поставке {supply_id}, статус оставлен без изменений")

        session.add_all(new_supplies)
        logger.info(f"✅ Добавлено новых поставок: {len(new_supplies)}")

        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "client_id": str(s.client_id),
                "status": s.status,  # Берём статус из БД, не меняем его
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
        """Регистрирует пользователя в API и БД, если его нет"""

        # ✅ Проверяем, есть ли пользователь в БД
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

        if user:
            logger.info(f"ℹ️ Пользователь {tg_id} уже существует в БД")
            return {"message": "Пользователь уже зарегистрирован"}

        # ✅ Отправляем запрос в API перед добавлением в БД
        async with aiohttp.ClientSession() as client:
            try:
                url = f"{self.BASE_URL}/catcher/register/user"
                async with client.post(url, params={"tg_id": tg_id}) as response:
                    response_json = await response.json()

                    if response.status == 200:
                        logger.info(f"✅ Пользователь {tg_id} зарегистрирован в API")
                    else:
                        logger.error(f"❌ Ошибка API регистрации: {response_json}")
                        return {
                            "error": "Ошибка регистрации на сервере. Попробуйте еще раз, отправив /start"
                        }

            except Exception as e:
                logger.error(f"❌ Ошибка подключения к API: {e}", exc_info=True)
                return {
                    "error": "Ошибка соединения с сервером. Попробуйте еще раз, отправив /start"
                }

        # ✅ Если регистрация в API успешна, добавляем пользователя в БД
        new_user = User(
            tg_id=tg_id,
            username=username if username else "unknown"
        )
        session.add(new_user)
        logger.info(f"✅ Пользователь {tg_id} ({new_user.username}) добавлен в БД")

        return {"message": "Пользователь зарегистрирован в системе"}

    @session_manager
    async def register_client(self, session, tg_id: int, name: str, cookies: str):
        """Регистрирует клиента через API и добавляет его в базу"""

        # ✅ Проверяем, есть ли уже кабинет с таким именем у пользователя
        existing_client = await self.get_client_by_name(tg_id, name)
        if existing_client:
            logger.info(f"⚠️ Кабинет {name} уже существует для пользователя {tg_id}")
            return {"error": "Кабинет уже зарегистрирован"}

        # ✅ Запрос к API для получения `client_id`
        async with aiohttp.ClientSession() as client:
            try:
                url = f"{self.BASE_URL}/catcher/register/client"
                async with client.post(url, params={"user_id": tg_id, "name": name, "cookies": cookies}) as response:
                    api_response = await response.json()

                    if response.status == 200:
                        client_id = api_response["client_id"]
                        logger.info(f"✅ API вернул client_id: {client_id}")

                        # ✅ Добавляем в базу
                        await self.add_client(tg_id=tg_id, client_id=client_id, name=name, cookies=cookies)

                        return {"message": "Кабинет зарегистрирован", "client_id": client_id}

                    else:
                        logger.error(f"❌ Ошибка API регистрации клиента: {api_response}")
                        return {"error": api_response.get("detail", "Ошибка при регистрации клиента")}

            except Exception as e:
                logger.error(f"❌ Ошибка подключения к API: {e}", exc_info=True)
                return {"error": "Ошибка связи с сервером. Попробуйте еще раз."}

    @session_manager
    async def confirm_supply_catching(
            self, session, supply_id: int, start_date: str, end_date: str, skip_dates: list, coefficient: float
    ):
        """Обновление информации о поставке при подтверждении отлова"""

        result = await session.execute(select(Supply).where(Supply.id == int(supply_id)))
        supply = result.scalars().first()

        if not supply:
            logger.warning(f"⚠️ Поставка с ID {supply_id} не найдена!")
            return {"error": f"Поставка с ID {supply_id} не найдена!"}

        # Преобразуем строки в datetime объекты
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            skip_dt_list = [datetime.fromisoformat(d) for d in skip_dates]
        except ValueError as e:
            logger.error(f"❌ Ошибка при преобразовании дат: {e}")
            return {"error": f"Ошибка при обработке дат: {e}"}

        # Обновляем поля
        supply.status = Status.CATCHING.value
        supply.start_catch_date = start_dt
        supply.end_catch_date = end_dt
        supply.skip_dates = skip_dt_list
        supply.coefficient = coefficient

        logger.info(
            f"✅ Поставка {supply_id} обновлена: статус={supply.status}, "
            f"start_catch_date={start_dt}, end_catch_date={end_dt}, "
            f"skip_dates={skip_dt_list}, coefficient={coefficient}"
        )

        return {"message": f"Поставка {supply_id} обновлена и отправлена на отлов"}

    @session_manager
    async def get_supply_by_id(self, session, supply_id: str):
        """Получаем поставку по ID"""
        result = await session.execute(select(Supply).where(Supply.id == int(supply_id)))
        return result.scalars().first()  # Возвращаем первую найденную поставку (или None, если не найдена)


