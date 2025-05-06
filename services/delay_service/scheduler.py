# services/delay_service/scheduler.py

from taskiq import TaskiqScheduler
from taskiq_redis import RedisScheduleSource
from taskiq_nats import PullBasedJetStreamBroker

from services.delay_service import tasks

# Инициализация брокера JetStream
broker = PullBasedJetStreamBroker(
    servers="nats://localhost:4222",
    queue="mailing_tasks",
)

# Redis как источник отложенных задач
redis_source = RedisScheduleSource("redis://localhost:6379/0")

# Планировщик, который знает, откуда брать задачи и куда их пихать
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[redis_source],
)

# Обязательно импортируем задачи, чтобы они зарегистрировались
from services.delay_service import tasks  # noqa
