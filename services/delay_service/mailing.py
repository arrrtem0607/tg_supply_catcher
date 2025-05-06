from database.controller.orm_instance import get_mailing_orm
from database.enums.mailing_status_enums import MailingStatus
from services.delay_service.broker import broker


orm = get_mailing_orm()


@broker.task
async def launch_mailing(mailing_id: str) -> None:
    """Запускает рассылку по ID: отправляет текст всем пользователям."""
    mailing = await orm.get_mailing(mailing_id)
    if not mailing or not mailing.is_active:
        return

    # Обновляем статус на IN_PROGRESS (начата)
    await orm.update_status(mailing_id, status=MailingStatus.IN_PROGRESS, start=True)

    # Шлём всем
    await orm.send_mailing(mailing)

    # Обновляем статус на COMPLETED (завершена)
    await orm.update_status(mailing_id, status=MailingStatus.COMPLETED, end=True)
