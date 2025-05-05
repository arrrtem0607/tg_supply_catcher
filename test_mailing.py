import asyncio
from datetime import datetime, timedelta, timezone

from database.entities.core import Database
from database.entities.models import Mailing, MailingStatus
from database.controller.mailing_controller import MailingController
from services.delay_service.tasks import launch_mailing

from bot.utils.logger import setup_logger

logger = setup_logger("test_mailing")

db = Database()
mailing_ctrl = MailingController(db)

async def main():
    async with db.session() as session:
        # Создаём тестовую рассылку
        new_mailing = Mailing(
            text="🧪 Это тестовая рассылка",
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=10),
            status=MailingStatus.SCHEDULED,
        )
        session.add(new_mailing)
        await session.commit()
        logger.info(f"📨 Тестовая рассылка создана: ID={new_mailing.id}")

        # Необязательно: сразу запускаем вручную (иначе подхватит планировщик)
        await launch_mailing.kiq(str(new_mailing.id))
        logger.info(f"🚀 launch_mailing.kiq вызван вручную")

if __name__ == "__main__":
    asyncio.run(main())
