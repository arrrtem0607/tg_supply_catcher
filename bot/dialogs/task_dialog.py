import operator
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button, ScrollingGroup
from aiogram_dialog.widgets.text import Jinja
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database.controller.ORM import ORMController
from bot.utils.statesform import ManageClientStates, MainMenu

import logging

logger = logging.getLogger(__name__)

orm_controller = ORMController()

PAGE_SIZE = 5  # Количество поставок на одной странице

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

async def get_supplies_list(dialog_manager: DialogManager, **kwargs):
    """Получает список поставок для выбранного кабинета с динамическим обновлением."""
    tg_id = dialog_manager.event.from_user.id
    client_id = dialog_manager.dialog_data.get("selected_client")

    if not client_id:
        return {"supplies": [], "supply_details": "❌ Нет данных по поставкам"}

    try:
        client_id = int(client_id)
    except ValueError:
        logger.error(f"❌ Ошибка приведения client_id ({client_id}) к int")
        return {"supplies": [], "supply_details": "❌ Ошибка получения данных"}

    # 🔥 Запрашиваем поставки
    supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)
    if not supplies:
        return {"supplies": [], "supply_details": "📦 Нет доступных поставок"}

    # 🔥 Получаем текущую страницу из состояния
    page = dialog_manager.dialog_data.get("supply_pagination", 0)

    # 🔥 Ограничиваем список поставок до текущей страницы
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_supplies = supplies[start_idx:end_idx]

    # 🔥 Проверяем, есть ли данные
    if not current_supplies:
        return {"supplies": [], "supply_details": "📦 На этой странице нет поставок."}

    # 🔥 Формируем текст для отображаемых поставок
    supply_info_text = "📦 <b>Информация о поставках:</b>\n\n"
    supply_list = []

    for supply in current_supplies:
        supply_id = supply.get("supplyId") or supply.get("preorderId", "Не указан")
        warehouse_name = supply.get("warehouseName", "Не указан")
        box_type = supply.get("boxTypeName", "Не указан")
        status = supply.get("statusName", "Неизвестный статус")

        supply_info_text += (
            f"🔹 <b>Поставка {supply_id}</b>\n"
            f"🏬 Склад: {warehouse_name}\n"
            f"📦 Тип: {box_type}\n"
            f"📌 Статус: {status}\n\n"
        )

        supply_list.append((str(supply_id), str(supply_id)))

    return {
        "supplies": supply_list,
        "supply_details": supply_info_text,
        "count": len(supply_list),
    }

async def on_page_change(event, widget, manager: DialogManager):
    """Обработчик смены страницы в ScrollingGroup"""
    current_page = await widget.get_page(manager)  # Получаем текущую страницу
    manager.dialog_data["supply_pagination"] = current_page  # Сохраняем в данные диалога
    await manager.next()  # Обновляем окно диалога

async def on_supply_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора поставки"""
    manager.dialog_data["selected_supply"] = item_id
    await manager.switch_to(ManageClientStates.SUPPLY_ACTIONS)


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
        Button(Jinja("📦 Поставки клиента"), id="client_supplies",
               on_click=lambda c, w, m: m.switch_to(ManageClientStates.CLIENT_SUPPLIES)),
        Button(Jinja("🔄 Обновить данные"), id="update_client",
               on_click=lambda c, w, m: m.switch_to(ManageClientStates.UPDATE_CLIENT)),
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(ManageClientStates.CHOOSE_CLIENT)),
        state=ManageClientStates.CHOOSE_ACTION,
        parse_mode="HTML",
    ),
    Window(
        Jinja("📦 <b>Информация о поставках:</b>\n\n{{ supply_details }}"),  # 🔥 Динамически обновляемый текст
        ScrollingGroup(
            Select(
                text=Jinja("📦 {{ item[0] }}"),  # 🔥 Кнопки с номером поставки
                id="select_supply",
                item_id_getter=operator.itemgetter(1),
                items="supplies",
                on_click=on_supply_selected,
            ),
            id="supply_pagination",
            width=1,  # Одна колонка
            height=PAGE_SIZE,  # 5 кнопок на страницу
            on_page_changed=on_page_change,  # 🔥 Обработчик смены страницы
        ),
        Button(
            Jinja("🔙 Назад"),
            id="back",
            on_click=lambda c, w, m: m.switch_to(ManageClientStates.CHOOSE_ACTION)
        ),
        state=ManageClientStates.CLIENT_SUPPLIES,
        getter=get_supplies_list,
        parse_mode="HTML",
    )
)
