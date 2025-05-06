from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq_redis.schedule_source import ScheduledTask

from configurations import get_config
from database.entities.core import Database
from database.db_utils import session_manager
from database.entities.models import Mailing, MailingStatus, User
from services.utils.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
bot = Bot(token=config.bot_config.get_token())


class MailingController:
    def __init__(self, db: Database = Database()):
        self.db = db

    # ────────────────────────────────
    # ▶️ Создание рассылки
    # ────────────────────────────────
    @session_manager
    async def create_mailing(self, session: AsyncSession, text: str, scheduled_at: datetime, recipients_ids: list[int] | None = None):
        from services.delay_service.redis_config import redis_source
        mailing = Mailing(
            text=text,
            scheduled_at=scheduled_at,
            status=MailingStatus.SCHEDULED,
        )

        if recipients_ids:
            users = (await session.execute(select(User).where(User.tg_id.in_(recipients_ids)))).scalars().all()
            mailing.recipients = users  # many-to-many
        else:
            # Если не указаны — рассылка для всех пользователей
            users = (await session.execute(select(User))).scalars().all()
            mailing.recipients = users

        session.add(mailing)
        await session.flush()

        task = ScheduledTask(
            task_name="launch_mailing_task",
            args=[str(mailing.id)],
            kwargs={},
            labels={},
            time=scheduled_at
        )
        await redis_source.add_schedule(task)
        logger.info(f"🗓️ Задача на рассылку добавлена в планировщик: {mailing.id}")

        return mailing

    # ────────────────────────────────
    # ▶️ Получение рассылки по ID
    # ────────────────────────────────
    @session_manager
    async def get_mailing(self, session: AsyncSession, mailing_id: str) -> Mailing | None:
        return await session.get(Mailing, mailing_id)

    # ────────────────────────────────
    # ▶️ Обновление статуса рассылки
    # ────────────────────────────────
    @session_manager
    async def update_status(self, session: AsyncSession, mailing_id: str, status: MailingStatus, start=False, end=False):
        mailing = await session.get(Mailing, mailing_id)
        if not mailing:
            return None

        mailing.status = status
        if start:
            mailing.started_at = datetime.now(timezone.utc)
        if end:
            mailing.finished_at = datetime.now(timezone.utc)

        await session.commit()
        return mailing

    # ────────────────────────────────
    # ▶️ Удаление запланированной рассылки
    # ────────────────────────────────
    @session_manager
    async def cancel_mailing(self, session: AsyncSession, mailing_id: str):
        mailing = await session.get(Mailing, mailing_id)
        if mailing:
            mailing.status = MailingStatus.CANCELLED
            mailing.is_active = False
            await session.commit()
            logger.info(f"❌ Рассылка отменена: {mailing_id}")
            return True
        return False

    # ────────────────────────────────
    # ▶️ Отправка сообщений пользователям
    # ────────────────────────────────
    async def send_mailing(self, mailing: Mailing):
        users = [u.tg_id for u in mailing.recipients]
        logger.info(f"📨 Рассылка {mailing.id} — всего пользователей: {len(users)}")

        success, failed = 0, 0

        for chat_id in users:
            try:
                await bot.send_message(chat_id=chat_id, text=mailing.text)
                success += 1
                logger.debug(f"✅ Отправлено пользователю {chat_id}")
            except Exception as e:
                failed += 1
                logger.warning(f"⚠️ Ошибка для {chat_id}: {e}")

        logger.info(f"📬 Рассылка завершена: успешно {success}, не удалось {failed}")

    # ────────────────────────────────
    # ▶️ Получение всех активных рассылок
    # ────────────────────────────────
    @session_manager
    async def get_scheduled_mailings(self, session: AsyncSession):
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Mailing).where(
                Mailing.scheduled_at <= now,
                Mailing.status == MailingStatus.SCHEDULED,
                Mailing.is_active.is_(True)
            )
        )
        return result.scalars().all()
