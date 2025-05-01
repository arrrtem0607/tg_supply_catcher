from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Jinja

from bot.utils.statesform import MainMenu, BalanceStates, InfoStates, AddClientStates, ManageClientStates
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database import get_orm

orm_controller = get_orm()

async def get_main_menu_data(dialog_manager: DialogManager, **kwargs):
    """Функция загрузки данных о балансе и тарифе пользователя из БД"""
    user_id = dialog_manager.event.from_user.id
    balance = await orm_controller.balance.get_balance(user_id)
    active_sub = await orm_controller.get_active_subscription(user_id)

    return {
        "balance": f"{balance:,}₽",  # Пробелы в числах
        "tariff": active_sub.tariff.name if active_sub else "Нет активной подписки",
    }


async def on_my_clients(callback: CallbackQuery, widget, manager: DialogManager):
    """Переход в диалог выбора кабинетов"""
    await manager.start(state=ManageClientStates.CHOOSE_CLIENT, show_mode=ShowMode.EDIT)


async def on_add_client(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик нажатия на кнопку '➕ Добавить кабинет'"""
    await manager.start(state=AddClientStates.ENTRY_METHOD, show_mode=ShowMode.EDIT)


async def on_price(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик нажатия на кнопку '💰 Прайс'"""
    await manager.start(state=BalanceStates.MAIN, show_mode=ShowMode.EDIT)


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
            Button(Jinja("💰 Цены и пополнение счета"), id="price", on_click=on_price),
            Button(Jinja("ℹ️ О сервисе"), id="info", on_click=on_info),
        ),
        state=MainMenu.MAIN_MENU,
        getter=get_main_menu_data,
        parse_mode="HTML",
    )
)
