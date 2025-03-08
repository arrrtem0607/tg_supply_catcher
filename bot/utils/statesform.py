from aiogram.fsm.state import StatesGroup, State

class MainMenu(StatesGroup):
    MAIN_MENU = State()  # 📌 Главное меню

class PriceStates(StatesGroup):
    PRICE_INFO = State()  # 💸 Окно с прайсом

class InfoStates(StatesGroup):
    ABOUT_SERVICE = State()  # ℹ️ О сервисе

from aiogram.fsm.state import StatesGroup, State

class ClientStates(StatesGroup):
    ENTER_NAME = State()  # Ввод имени кабинета
    SEND_INSTRUCTION = State()  # Инструкция по выгрузке Cookies
    ENTER_COOKIES = State()  # Ввод Cookies
    CONFIRMATION = State()  # Подтверждение добавления


class SupplyStates(StatesGroup):
    CHOOSE_SUPPLY = State()  # 📦 Выбор поставки
    SUPPLY_ACTIONS = State()  # 🔄 Действия с поставкой
