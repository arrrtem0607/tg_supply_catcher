from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database.entities.models import Mailing, MailingStatus, User
from database.entities.core import Database
from configurations import get_config
from database.db_utils import session_manager
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
bot = Bot(token=config.bot_config.get_token())


class MailingController:
    def __init__(self, db: Database = Database()):
        self.db = db

    @staticmethod
    async def send_mailing(session: AsyncSession, mailing: Mailing):
        users = (await session.execute(select(User.tg_id))).scalars().all()
        logger.info(f"📨 Рассылка {mailing.id}: найдено {len(users)} пользователей")

        success = 0
        failed = 0

        for chat_id in users:
            try:
                await bot.send_message(chat_id=chat_id, text=mailing.text)
                success += 1
                logger.debug(f"✅ Отправлено сообщение пользователю {chat_id}")
            except Exception as e:
                failed += 1
                logger.warning(f"⚠️ Ошибка отправки для пользователя {chat_id}: {e}")

        logger.info(
            f"📬 Рассылка {mailing.id} завершена: "
            f"успешно {success}, не удалось {failed}"
        )

    @session_manager
    async def get_scheduled_mailings(self, session):
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Mailing).where(
                Mailing.scheduled_at <= now,
                Mailing.status == MailingStatus.SCHEDULED,
                Mailing.is_active.is_(True)
            )
        )
        return result.scalars().all()