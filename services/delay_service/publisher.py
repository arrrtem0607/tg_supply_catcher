from datetime import datetime
from nats.js.client import JetStreamContext


async def delay_message_action(
    js: JetStreamContext,
    subject: str,
    chat_id: int,
    delay: int,
    action: str,
    text: str | None = None,
    message_id: int | None = None,
) -> None:
    """
    Публикует задачу в JetStream с нужным действием: send / delete

    :param js: JetStream-контекст
    :param subject: Сабджект, куда публикуем
    :param chat_id: Telegram chat_id
    :param delay: Задержка в секундах
    :param action: "send" или "delete"
    :param text: текст сообщения (только для send)
    :param message_id: ID сообщения для удаления (только для delete)
    """

    headers = {
        "Tg-Delayed-Chat-ID": str(chat_id),
        "Tg-Delayed-Msg-Timestamp": str(datetime.now().timestamp()),
        "Tg-Delayed-Msg-Delay": str(delay),
        "Tg-Action": action
    }

    if action == "send" and text:
        headers["Tg-Delayed-Msg-Text"] = text

    if action == "delete" and message_id:
        headers["Tg-Delayed-Msg-ID"] = str(message_id)

    await js.publish(subject=subject, headers=headers)
