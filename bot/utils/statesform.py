from aiogram.fsm.state import StatesGroup, State

class MainMenu(StatesGroup):
    MAIN_MENU = State()  # 📌 Главное меню

class PriceStates(StatesGroup):
    PRICE_INFO = State()  # 💸 Окно с прайсом

class InfoStates(StatesGroup):
    ABOUT_SERVICE = State()  # ℹ️ О сервисе

class AddClientStates(StatesGroup):
    """Состояния для добавления кабинета"""
    ENTER_NAME = State()  # Ввод имени кабинета
    ENTER_COOKIES = State()  # Ввод Cookies
    CONFIRMATION = State()  # Подтверждение добавления

class ManageClientStates(StatesGroup):
    CHOOSE_CLIENT = State()  # Выбор кабинета
    CHOOSE_ACTION = State()  # Выбор действия с кабинетом
    CLIENT_SUPPLIES = State()  # 📦 Просмотр поставок
    SUPPLY_ACTIONS = State()  # Действия с выбранной поставкой
    UPDATE_CLIENT = State()  # 🔄 Обновление данных

class SupplyStates(StatesGroup):
    CHOOSE_SUPPLY = State()  # 📦 Выбор поставки
    SUPPLY_ACTIONS = State()  # 🔄 Действия с поставкой
