from aiogram.fsm.state import StatesGroup, State

class MainMenu(StatesGroup):
    MAIN_MENU = State()  # 📌 Главное меню

class PriceStates(StatesGroup):
    PRICE_INFO = State()  # 💸 Окно с прайсом

class InfoStates(StatesGroup):
    ABOUT_SERVICE = State()  # ℹ️ О сервисе

class AddClientStates(StatesGroup):
    """Состояния для добавления кабинета"""
    ENTRY_METHOD = State()
    ENTER_NAME = State()  # Ввод имени кабинета
    ENTER_PHONE = State()
    ENTER_COOKIES = State()  # Ввод Cookies
    CONFIRMATION = State()  # Подтверждение добавления
    ENTER_SMS_CODE = State()


class ManageClientStates(StatesGroup):
    CHOOSE_CLIENT = State()  # Выбор кабинета
    CLIENT_SUPPLIES = State()  # 📦 Просмотр поставок
    CHOOSE_ACTION = State()
    SUPPLY_ACTIONS = State()  # Действия с выбранной поставкой
    UPDATE_CLIENT = State()  # 🔄 Обновление данных
    CHOOSE_SUPPLY = State()  # 📦 Выбор поставки
    ACTIVE_TASKS = State()
    ENTER_NEW_NAME = State()
    ENTER_NEW_COOKIES = State()

class SupplyStates(StatesGroup):
    CHOOSE_SUPPLY_ACTION = State()
    CHOOSE_COEFFICIENT = State()
    CHOOSE_START_DATE = State()
    CHOOSE_END_DATE = State()
    CHOOSE_SKIP_DATES = State()
    CONFIRM = State()



