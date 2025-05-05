import logging
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)


class DelayedMessageConsumer:
    def __init__(
        self,
        nc: Client,
        js: JetStreamContext,
        bot: Bot,
        subject: str,
        stream: str,
        durable_name: str
    ) -> None:
        self.nc = nc
        self.js = js
        self.bot = bot
        self.subject = subject
        self.stream = stream
        self.durable_name = durable_name
        self.stream_sub = None

    async def start(self) -> None:
        self.stream_sub = await self.js.subscribe(
            subject=self.subject,
            stream=self.stream,
            cb=self.on_message,
            durable=self.durable_name,
            manual_ack=True
        )
        logger.info(f"Subscribed to NATS subject: {self.subject}")

    async def on_message(self, msg: Msg):
        headers = msg.headers

        try:
            sent_time = datetime.fromtimestamp(float(headers.get("Tg-Delayed-Msg-Timestamp")), tz=timezone.utc)
            delay = int(headers.get("Tg-Delayed-Msg-Delay"))
            action = headers.get("Tg-Action")
        except Exception as e:
            logger.error(f"Invalid headers in message: {headers} — {e}")
            await msg.ack()
            return

        now = datetime.now().astimezone()
        ready_at = sent_time + timedelta(seconds=delay)

        if ready_at > now:
            # ещё не наступило время
            retry_delay = (ready_at - now).total_seconds()
            await msg.nak(delay=retry_delay)
            return

        try:
            chat_id = int(headers.get("Tg-Delayed-Chat-ID"))

            if action == "delete":
                message_id = int(headers.get("Tg-Delayed-Msg-ID"))
                with suppress(TelegramBadRequest):
                    await self.bot.delete_message(chat_id=chat_id, message_id=message_id)

            elif action == "send":
                text = headers.get("Tg-Delayed-Msg-Text")
                if text:
                    await self.bot.send_message(chat_id=chat_id, text=text)

            else:
                logger.warning(f"Unknown action '{action}' in message headers: {headers}")

        except Exception as e:
            logger.exception(f"Error while processing delayed message: {e}")

        await msg.ack()

    async def unsubscribe(self) -> None:
        if self.stream_sub:
            await self.stream_sub.unsubscribe()
            logger.info('Consumer unsubscribed from stream')
