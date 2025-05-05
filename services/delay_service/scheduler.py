from taskiq import TaskiqScheduler
from taskiq.schedule_sources import AsyncScheduleSource
from taskiq_nats import NatsBroker

from services.delay_service.tasks import launch_mailing
from bot.utils.logger import setup_logger
from database.controller.mailing_controller import MailingController
from database.entities.core import Database

logger = setup_logger(__name__)

broker = NatsBroker("nats://localhost:4222")
db = Database()
mailing_ctrl = MailingController(db)

class MailingScheduleSource(AsyncScheduleSource):
    async def get_current_schedules(self):
        """
        Планировщик запускает рассылки со статусом 'scheduled'
        """
        mailings = await mailing_ctrl.get_scheduled_mailings()

        schedules = []
        for mailing in mailings:
            logger.info(f"📅 Планировщик: найдено запланированное mailing_id={mailing.id}")
            schedules.append(launch_mailing.with_args(str(mailing.id)))

        return schedules

scheduler = TaskiqScheduler(broker=broker, sources=[MailingScheduleSource()])
