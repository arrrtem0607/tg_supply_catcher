from services.utils.logger import setup_logger

logger = setup_logger(__name__)

def session_manager(func):
    async def wrapper(self, *args, **kwargs):
        async with self.db.session() as session:
            async with session.begin():
                try:
                    result = await func(self, session, *args, **kwargs)
                    await session.commit()
                    logger.debug(f"✅ {func.__name__} выполнена успешно")
                    return result
                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ Ошибка в {func.__name__}: {e}", exc_info=True)
                    raise e
    return wrapper