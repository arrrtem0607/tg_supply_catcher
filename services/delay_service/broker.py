from taskiq_nats import PullBasedJetStreamBroker

broker = PullBasedJetStreamBroker(
    servers="nats://localhost:4222",
    queue="mailing_queue",
    stream="MAILING_STREAM",
    subject="mailing_queue.tasks",
    durable="MAILING_CONSUMER",
)
