from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from database.db_utils import session_manager
from database.entities.models import Supply, Client
from database.enums import Status
from services.utils.logger import setup_logger

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

class SupplyController:
    def __init__(self):
        logger.info("SupplyController initialized")

    @session_manager
    async def get_supplies_by_client(self, session, user_id: int, client_id: str):
        result = await session.execute(
            select(Client).where(Client.client_id == client_id, Client.user_id == user_id)
        )
        client = result.scalars().first()
        if not client:
            return []

        db_supplies = await session.execute(
            select(Supply)
            .options(joinedload(Supply.client), joinedload(Supply.user))
            .where(Supply.client_id == client_id, Supply.user_id == user_id)
        )
        return [s.to_dict() for s in db_supplies.scalars().all()]

    @session_manager
    async def get_supply_by_id(self, session, user_id: int, preorder_id: int):
        result = await session.execute(
            select(Supply).where(Supply.user_id == user_id, Supply.preorder_id == preorder_id)
        )
        return result.scalars().first()

    @session_manager
    async def update_status_by_preorder_id(self, session, preorder_id: int, new_status: Status):
        result = await session.execute(
            update(Supply)
            .where(Supply.preorder_id == preorder_id)
            .values(status=new_status)
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            logger.warning(f"⚠️ Поставки с preorder_id={preorder_id} не найдены!")
            return {"error": f"Поставки с preorder_id {preorder_id} не найдены!"}

        logger.info(f"✅ Обновлен статус поставок с preorder_id={preorder_id} на {new_status.name}")
        return {"message": f"Статус всех поставок с preorder_id={preorder_id} обновлен на {new_status.name}"}
