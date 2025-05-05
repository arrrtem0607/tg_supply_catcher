from datetime import datetime
from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Jinja

from bot.utils.statesform import MainMenu, BalanceStates, InfoStates, AddClientStates, ManageClientStates
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database.controller.orm_instance import get_orm

orm_controller = get_orm()


async def get_main_menu_data(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.event.from_user.id
    balance = await orm_controller.balance.get_balance(user_id)
    sub = await orm_controller.get_active_subscription(user_id)

    if sub:
        days_left = (sub.end_date - datetime.utcnow()).days
        return {
            "balance": f"{balance:,}₽",
            "subscription_end": sub.end_date.strftime("%d.%m.%Y"),
            "days_left": days_left,
        }
    else:
        return {
            "balance": f"{balance:,}₽",
            "subscription_end": None,
            "days_left": None,
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
        Jinja("""
<b>🔹 Главное меню 🔹</b>

<code>💰 Баланс:      {{ balance }}</code>
<code>📜 Подписка до: {{ subscription_end or '—' }}</code>
<code>⏳ Осталось:     {{ days_left or '—' }} дн.</code>

Выберите действие:
            """),
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
