import asyncio
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.payments.service import router as webhook_router
from services.payments.client import TochkaAPIClient
from configurations.payments_config import PaymentsConfig
from services.utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(5)
    client = TochkaAPIClient(PaymentsConfig())
    try:
        url = "https://5b6c-45-144-233-139.ngrok-free.app/webhook/tochka/"  # 🔄 заменить на актуальный
        await client.setup_webhook(url)
        logger.info("✅ Вебхук Точки успешно зарегистрирован")
    except Exception as e:
        logger.error("❌ Ошибка при регистрации вебхука Точки: %s", e)

    yield

    try:
        await client.delete_webhook()
        logger.info("🗑️ Вебхук Точки удалён при завершении работы")
    except Exception as e:
        logger.error("❌ Не удалось удалить вебхук Точки: %s", e)

# FastAPI app для оплаты
payment_api = FastAPI(lifespan=lifespan)
payment_api.include_router(webhook_router)

async def main():
    config = uvicorn.Config(payment_api, host="0.0.0.0", port=8010, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
