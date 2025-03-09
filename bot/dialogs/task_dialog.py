import operator
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.text import Jinja
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database.controller.ORM import ORMController
from bot.utils.statesform import ManageClientStates, MainMenu

orm_controller = ORMController()

async def get_clients_list(dialog_manager: DialogManager, **kwargs):
    """Получение списка кабинетов пользователя"""
    tg_id = dialog_manager.event.from_user.id
    clients = await orm_controller.get_clients_by_user_id(tg_id)

    client_list = [(client.name, client.client_id) for client in clients]

    return {"clients": client_list, "count": len(client_list)}

async def on_client_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора кабинета"""
    manager.dialog_data["selected_client"] = item_id
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION)

async def on_my_clients(callback: CallbackQuery, widget, manager: DialogManager):
    """Открываем список кабинетов пользователя"""
    await manager.start(ManageClientStates.CHOOSE_CLIENT)

task_dialog = Dialog(
    # Окно выбора кабинета
    Window(
        Jinja(
            "👥 <b>Выберите кабинет:</b>\n\n"
            "{% for client in clients %}🔹 <b>{{ client[0] }}</b> (ID: {{ client[1] }})\n{% endfor %}"
        ),
        Select(
            text=Jinja("🔹 {{ item[0] }}"),
            id="select_client",
            item_id_getter=operator.itemgetter(1),
            items="clients",
            on_click=on_client_selected,
        ),
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        state=ManageClientStates.CHOOSE_CLIENT,
        getter=get_clients_list,
        parse_mode="HTML",
    ),

    # Окно с действиями над выбранным кабинетом
    Window(
        Jinja(
            "🔹 <b>Выбран кабинет:</b> {{ selected_client }}\n\n"
            "Выберите действие:"
        ),
        Button(Jinja("📦 Поставки клиента"), id="client_supplies", on_click=lambda c, w, m: m.switch_to(ManageClientStates.CLIENT_SUPPLIES)),
        Button(Jinja("🔄 Обновить данные"), id="update_client", on_click=lambda c, w, m: m.switch_to(ManageClientStates.UPDATE_CLIENT)),
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(ManageClientStates.CHOOSE_CLIENT)),
        state=ManageClientStates.CHOOSE_ACTION,
        parse_mode="HTML",
    ),
)
