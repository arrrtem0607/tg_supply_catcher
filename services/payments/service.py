from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from database.controller.orm_instance import get_orm
from services.utils.logger import setup_logger

router = APIRouter(prefix="/webhook/tochka")
logger = setup_logger(__name__)

orm_controller = get_orm()

@router.post("/")
async def handle_payment_webhook(request: Request):
    try:
        body = await request.json()
        logger.info("✅ Получен вебхук от Точки: %s", body)

        operations = body.get("Data", {}).get("Operation")
        if not operations:
            return JSONResponse(status_code=400, content={"error": "No operations found"})

        for op in operations:
            status_ = op.get("status")
            purpose = op.get("purpose")
            amount = op.get("amount")

            if not (status_ and purpose and amount):
                continue

            if status_ != "APPROVED":
                continue

            # Извлечение Telegram ID
            try:
                if "Telegram ID" in purpose:
                    user_id = int(purpose.split("Telegram ID")[-1].strip())
                else:
                    logger.warning("⚠️ Невозможно извлечь Telegram ID из purpose: %s", purpose)
                    continue
            except Exception as e:
                logger.warning("⚠️ Ошибка извлечения user_id: %s", e)
                continue

            try:
                await orm_controller.balance.add_balance(user_id=user_id, amount=float(amount))
                logger.info("💰 Баланс пользователя %s пополнен на %s₽", user_id, amount)
            except Exception as e:
                logger.error("❌ Ошибка при пополнении баланса пользователя %s: %s", user_id, e)

        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Webhook processed"})

    except Exception as e:
        logger.exception("❌ Ошибка при обработке вебхука")
        return JSONResponse(status_code=500, content={"error": str(e)})
