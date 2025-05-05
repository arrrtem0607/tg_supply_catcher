from datetime import datetime
from aiogram import Bot
from database.entities.core import Database
from database.entities.models import Mailing, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq_nats import NatsBroker

from configurations import get_config
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
bot = Bot(token=config.bot_config.get_token())
broker = NatsBroker("nats://localhost:4222")

db = Database()

@broker.task
async def launch_mailing(mailing_id: str) -> None:
    logger.info(f"🚀 Запуск рассылки: {mailing_id}")
    async with db.session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing:
            logger.error(f"❌ Рассылка {mailing_id} не найдена")
            return

        mailing.started_at = datetime.now()
        mailing.status = "in_progress"
        await session.commit()

        try:
            await _send_mailing(session, mailing)
            mailing.status = "completed"
            logger.info(f"✅ Рассылка {mailing_id} завершена успешно")
        except Exception as e:
            mailing.status = "failed"
            logger.exception(f"❌ Ошибка при рассылке {mailing_id}: {e}")
        finally:
            mailing.finished_at = datetime.now()
            await session.commit()


async def _send_mailing(session: AsyncSession, mailing: Mailing):
    users = (await session.execute(select(User.tg_id))).scalars().all()
    logger.info(f"📨 Рассылка {mailing.id} — всего пользователей: {len(users)}")

    success = 0
    fail = 0

    for chat_id in users:
        try:
            await bot.send_message(chat_id=chat_id, text=mailing.text)
            success += 1
        except Exception as e:
            fail += 1
            logger.warning(f"⚠️ Ошибка отправки {chat_id}: {e}")

    logger.info(f"📬 Завершено. Успешно: {success}, ошибок: {fail}")
