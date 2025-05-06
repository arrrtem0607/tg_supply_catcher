import asyncio
from datetime import datetime, timedelta, timezone

from database.controller.orm_instance import get_mailing_orm
from services.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    orm = get_mailing_orm()

    scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=10)

    mailing = await orm.create_mailing(
        text="📢 Это тестовая рассылка!",
        scheduled_at=scheduled_time,
        recipients_ids=None,  # можно указать список ID
    )

    logger.info(f"✅ Рассылка создана: {mailing.id} (отправка в {scheduled_time.isoformat()})")


if __name__ == "__main__":
    asyncio.run(main())
