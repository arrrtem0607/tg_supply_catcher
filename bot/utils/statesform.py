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
    CHOOSE_SUPPLY = State()  # 📦 Выбор поставки
    CHOOSE_SUPPLY_ACTION = State()
    CHOOSE_COEFFICIENT = State()
    CHOOSE_START_DATE = State()
    CHOOSE_END_DATE = State()
    CHOOSE_SKIP_DATES = State()
    CONFIRM = State()


