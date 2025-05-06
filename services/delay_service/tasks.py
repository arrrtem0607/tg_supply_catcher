from datetime import timedelta

from services.delay_service.broker import broker
from services.delay_service.launch_mailing import launch_mailing


@broker.task(schedule=[(timedelta(seconds=5),)])
async def scheduled_launch_mailing(mailing_id: str) -> None:
    await launch_mailing(mailing_id)
