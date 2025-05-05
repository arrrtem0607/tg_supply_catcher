from database.controller.ORM import ORMController

_orm_instance = None

def get_orm() -> ORMController:
    global _orm_instance
    if _orm_instance is None:
        _orm_instance = ORMController()
    return _orm_instance
