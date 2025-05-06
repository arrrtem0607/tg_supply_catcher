# database/controller/orm_instance.py
from database.controller.ORM import ORMController
from database.controller.mailing_controller import MailingController
from database.controller.balance_controller import BalanceController
_orm_instance = None

def get_orm() -> ORMController:
    global _orm_instance
    if _orm_instance is None:
        _orm_instance = ORMController()
    return _orm_instance

def get_mailing_orm() -> MailingController:
    global _orm_instance
    if _orm_instance is None:
        _orm_instance = MailingController()
    return _orm_instance

def get_balance_orm() -> BalanceController:
    global _orm_instance
    if _orm_instance is None:
        _orm_instance = BalanceController()
        return _orm_instance
    return _orm_instance