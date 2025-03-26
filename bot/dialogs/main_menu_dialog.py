from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Jinja

from bot.utils.statesform import MainMenu, PriceStates, InfoStates, AddClientStates, ManageClientStates
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery


async def get_main_menu_data(dialog_manager: DialogManager, **kwargs):
    """Функция загрузки данных о балансе и тарифе пользователя из БД"""
    user_data = {
        "balance": "25 000₽",  # Подтягиваем из БД
        "tariff": "Месячная подписка",  # Подтягиваем тариф
    }
    return user_data


async def on_my_clients(callback: CallbackQuery, widget, manager: DialogManager):
    """Переход в диалог выбора кабинетов"""
    await manager.start(state=ManageClientStates.CHOOSE_CLIENT, show_mode=ShowMode.EDIT)


async def on_add_client(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик нажатия на кнопку '➕ Добавить кабинет'"""
    await manager.start(state=AddClientStates.ENTER_NAME, show_mode=ShowMode.EDIT)  # ✅ Переход в состояние добавления кабинета


async def on_price(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик нажатия на кнопку '💰 Прайс'"""
    await manager.start(state=PriceStates.PRICE_INFO, show_mode=ShowMode.EDIT)


async def on_info(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик нажатия на кнопку 'ℹ️ О сервисе'"""
    await manager.start(state=InfoStates.ABOUT_SERVICE, show_mode=ShowMode.EDIT)


main_menu_dialog = Dialog(
    Window(
        Jinja(
            "🔹 <b>Главное меню</b>\n\n"
            "💰 <b>Баланс:</b> {{ balance }}\n"
            "📜 <b>Тариф:</b> {{ tariff }}\n\n"
            "Выберите действие:"
        ),
        Column(
            Button(Jinja("👥 Мои кабинеты"), id="my_clients", on_click=on_my_clients),
            Button(Jinja("➕ Добавить кабинет"), id="add_client", on_click=on_add_client),
            Button(Jinja("💰 Прайс"), id="price", on_click=on_price),
            Button(Jinja("ℹ️ О сервисе"), id="info", on_click=on_info),
        ),
        state=MainMenu.MAIN_MENU,
        getter=get_main_menu_data,  # Загружаем баланс и тариф
        parse_mode="HTML",  # Включаем HTML-разметку
    )
)
