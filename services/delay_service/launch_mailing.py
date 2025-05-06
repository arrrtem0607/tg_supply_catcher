from database.controller.mailing_controller import MailingController
from database.enums.mailing_status_enums import MailingStatus
import logging

logger = logging.getLogger(__name__)


async def launch_mailing(mailing_id: str) -> None:
    """Запускает рассылку по ID: отправляет текст всем пользователям."""
    orm = MailingController()

    try:
        # Получаем рассылку по ID
        mailing = await orm.get_mailing(mailing_id)
        if not mailing or not mailing.is_active:
            return

        # Обновляем статус: начата
        await orm.update_status(mailing_id, status=MailingStatus.IN_PROGRESS, start=True)

        # Отправляем сообщения
        await orm.send_mailing(mailing)

        # Обновляем статус: завершена
        await orm.update_status(mailing_id, status=MailingStatus.COMPLETED, end=True)

    except Exception as e:
        logger.exception(f"Ошибка при запуске рассылки {mailing_id}: {e}")
        await orm.update_status(mailing_id, status=MailingStatus.FAILED, end=True)
