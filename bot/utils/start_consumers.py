from services.delay_service.consumer import DelayedMessageConsumer

async def start_delayed_consumer(nc, js, bot, subject, stream, durable_name):
    consumer = DelayedMessageConsumer(
        nc=nc,
        js=js,
        bot=bot,
        subject=subject,
        stream=stream,
        durable_name=durable_name
    )
    await consumer.start()
