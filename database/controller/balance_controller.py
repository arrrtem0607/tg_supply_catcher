from sqlalchemy import select

from database.entities.models import ClientBalance
from database.entities.core import Database
from database.db_utils import session_manager
from bot.utils.logger import setup_logger

logger = setup_logger(__name__)


class BalanceController:
    def __init__(self, db: Database = Database()):
        self.db = db
        logger.info("BalanceController initialized")

    @session_manager
    async def get_balance(self, session, user_id: int) -> int:
        result = await session.execute(select(ClientBalance).where(ClientBalance.user_id == user_id))
        balance = result.scalars().first()
        return balance.balance if balance else 0

    @session_manager
    async def add_balance(self, session, user_id: int, amount: int):
        result = await session.execute(select(ClientBalance).where(ClientBalance.user_id == user_id))
        balance = result.scalars().first()
        if not balance:
            balance = ClientBalance(user_id=user_id, balance=0)
            session.add(balance)
        balance.balance += amount
        logger.info(f"💰 Пополнение баланса: user_id={user_id}, +{amount}")
        return balance.balance

    @session_manager
    async def deduct_balance(self, session, user_id: int, amount: int) -> bool:
        result = await session.execute(select(ClientBalance).where(ClientBalance.user_id == user_id))
        balance = result.scalars().first()
        if not balance or balance.balance < amount:
            logger.warning(f"🚫 Недостаточно средств: user_id={user_id}, требуется {amount}, есть {balance.balance if balance else 0}")
            return False
        balance.balance -= amount
        logger.info(f"💸 Списание баланса: user_id={user_id}, -{amount}")
        return True
