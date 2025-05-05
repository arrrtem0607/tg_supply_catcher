import nats
from nats.aio.client import Client
from nats.js import JetStreamContext


async def connect_to_nats(servers: list[str]) -> tuple[Client, JetStreamContext]:
    """
    Подключение к NATS и получение JetStream-контекста.

    :param servers: список адресов NATS-серверов (например: ["nats://localhost:4222"])
    :return: кортеж из клиента NATS и JetStream контекста
    """
    nc: Client = await nats.connect(servers)
    js: JetStreamContext = nc.jetstream()
    return nc, js
