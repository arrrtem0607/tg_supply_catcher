import operator
import logging

from aiogram import types
from aiogram_dialog import Dialog, Window, ShowMode, StartMode, DialogManager
from aiogram_dialog.widgets.kbd import Select, Button, ScrollingGroup
from aiogram_dialog.widgets.text import Jinja, List, Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram.types import CallbackQuery

from database.controller.ORM import ORMController
from bot.utils.statesform import ManageClientStates, MainMenu, AddClientStates, SupplyStates
from bot.utils.castom_scroll import sync_scroll, ManagedScroll
from bot.enums.status_enums import Status

logger = logging.getLogger(__name__)

orm_controller = ORMController()

PAGE_SIZE = 5  # Количество поставок на одной странице

async def get_clients_list(dialog_manager: DialogManager, **kwargs):
    """Получение списка кабинетов пользователя"""
    tg_id = dialog_manager.event.from_user.id
    clients = await orm_controller.get_clients_by_user_id(tg_id)

    if not clients:
        return {"clients": [], "count": 0, "no_clients": True}

    client_list = [(client.name, client.client_id) for client in clients]
    return {"clients": client_list, "count": len(client_list), "no_clients": False}

async def on_client_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора кабинета"""
    clients = await orm_controller.get_clients_by_user_id(callback.from_user.id)
    client = next((c for c in clients if str(c.client_id) == item_id), None)

    if client:
        manager.dialog_data["selected_client"] = str(client.client_id)
        manager.dialog_data["selected_client_name"] = client.name
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.EDIT)

async def get_selected_client(dialog_manager: DialogManager, **kwargs):
    return {
        "selected_client": dialog_manager.dialog_data.get("selected_client"),
        "selected_client_name": dialog_manager.dialog_data.get("selected_client_name", "❌ Неизвестно"),
    }

async def on_my_clients(callback: CallbackQuery, widget, manager: DialogManager):
    """Открываем список кабинетов пользователя"""
    await manager.start(ManageClientStates.CHOOSE_CLIENT, show_mode=ShowMode.EDIT)

async def get_supplies_list(dialog_manager: DialogManager, **kwargs):
    tg_id = dialog_manager.event.from_user.id
    client_id = dialog_manager.dialog_data.get("selected_client")

    if not client_id:
        return {"supplies": [], "supply_details": []}

    db_supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)

    if not db_supplies:
        return {"supplies": [], "supply_details": ["📦 Нет поставок."]}

    db_supplies = sorted(db_supplies, key=lambda x: x.get("api_created_at", ""), reverse=True)

    supply_list = []
    supply_text_list = []

    for supply in db_supplies:
        supply_id = str(supply.get("id", "❌ Без ID"))
        warehouse_name = supply.get("warehouse_name", "❌ Неизвестный склад")
        box_type = supply.get("box_type", "❌ Неизвестный тип")
        status_enum = Status.from_str(supply.get("status", ""))
        status_rus = status_enum.get_translation() if status_enum else "❌ Неизвестный статус"

        supply_list.append((supply_id, supply_id))
        supply_text_list.append(
            f"🔹 <b>Поставка {supply_id}</b>\n"
            f"🏬 Склад: {warehouse_name}\n"
            f"📦 Тип: {box_type}\n"
            f"📌 Статус: {status_rus}"
        )

    return {
        "supplies": supply_list,
        "supply_details": supply_text_list
    }

async def get_active_catching_tasks(dialog_manager: DialogManager, **kwargs):
    from bot.enums.status_enums import Status

    client_id = dialog_manager.dialog_data.get("selected_client")
    tg_id = dialog_manager.event.from_user.id

    if not client_id:
        return {
            "supplies": [],
            "supply_details": ["❌ Не выбран кабинет или client_id не указан."]
        }

    all_supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)
    catching_supplies = [
        s for s in all_supplies
        if Status.from_str(s.get("status")) == Status.CATCHING
    ]

    if not catching_supplies:
        return {
            "supplies": [],
            "supply_details": ["❌ Нет активных задач на отлов."]
        }

    supply_list = []
    supply_text_list = []

    for supply in catching_supplies:
        supply_id = str(supply.get("id", "❌ Без ID"))
        warehouse_name = supply.get("warehouse_name", "❌ Неизвестный склад")
        box_type = supply.get("box_type", "❌ Неизвестный тип")
        status_enum = Status.from_str(supply.get("status", ""))
        status_rus = status_enum.get_translation() if status_enum else "❌ Неизвестный статус"

        start = supply.get("start_catch_date", "—")
        end = supply.get("end_catch_date", "—")

        period = f"{start[:10]} → {end[:10]}" if start and end else "—"

        supply_list.append((supply_id, supply_id))
        supply_text_list.append(
            f"🎯 <b>Поставка {supply_id}</b>\n"
            f"🏬 Склад: {warehouse_name}\n"
            f"📦 Тип: {box_type}\n"
            f"📌 Статус: {status_rus}\n"
            f"🗓️ Период: {period}"
        )

    return {
        "supplies": supply_list,
        "supply_details": supply_text_list
    }

async def on_page_change(event: CallbackQuery, widget: ManagedScroll, manager: DialogManager, new_page: int):
    """Обновление списка поставок при смене страницы"""

    manager.dialog_data["supply_pagination"] = new_page
    supplies = manager.dialog_data.get("cached_supplies", [])

    # Формируем список поставок для текущей страницы
    start_idx = new_page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_supplies = supplies[start_idx:end_idx]

    if not current_supplies:
        supply_info_text = "📦 <b>Нет поставок для отображения.</b>"
        supply_list = []
    else:
        supply_info_text = "📦 <b>Информация о поставках:</b>\n\n"
        supply_list = []

        for supply in current_supplies:
            supply_id = str(supply.get("supplyId") or supply.get("preorderId", "Не указан"))
            warehouse_name = supply.get("warehouseName", "Не указан")
            box_type = supply.get("boxTypeName", "Не указан")
            status = supply.get("statusName", "Неизвестный статус")
            reject_reason = supply.get("rejectReason", "Причина не указана")

            supply_info_text += (
                f"🔹 <b>Поставка {supply_id}</b>\n"
                f"🏬 Склад: {warehouse_name}\n"
                f"📦 Тип: {box_type}\n"
                f"📌 Статус: {status}\n"
                f"❌ Причина отклонения: {reject_reason}\n\n"
            )

            supply_list.append((supply_id, supply_id))

    manager.dialog_data["supply_details"] = supply_info_text.strip()
    manager.dialog_data["supplies"] = supply_list

    await manager.show()  # Обновляем интерфейс

async def on_add_client(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик кнопки добавления кабинета"""
    await manager.start(AddClientStates.ENTRY_METHOD, show_mode=ShowMode.EDIT)

async def on_back_pressed(manager: DialogManager):
    """Удаляет только кешированные поставки и возвращает в главное меню"""
    manager.dialog_data.pop("cached_supplies", None)  # Удаляем только кэш поставок, если он есть
    manager.dialog_data.pop("supply_pagination", None)  # Также сбрасываем номер страницы
    await manager.back(show_mode=ShowMode.EDIT)  # Возвращаем в главное меню

async def on_supply_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора поставки (и перехода в supply_dialog)."""

    supply_id = item_id
    client_id = manager.dialog_data.get("selected_client")

    if not client_id:
        await callback.message.answer("❌ Не выбран клиент.")
        return

    logger.info(f"Переход к supply_dialog с поставкой {supply_id}, client_id={client_id}")

    await manager.start(
        state=SupplyStates.CHOOSE_SUPPLY_ACTION,
        data={"supply_id": supply_id, "client_id": client_id},
        mode=StartMode.NORMAL,
        show_mode=ShowMode.EDIT,
    )

async def get_active_tasks(dialog_manager: DialogManager, **kwargs):
    tg_id = dialog_manager.event.from_user.id
    client_id = dialog_manager.dialog_data.get("selected_client")

    if not client_id:
        return {"tasks": [], "selected_client_name": "❓ Неизвестно"}

    all_supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)
    catching_tasks = [
        {
            "id": supply["id"],
            "status": Status.from_str(supply["status"]).get_translation(),
            "start": supply.get("start_catch_date", "—"),
            "end": supply.get("end_catch_date", "—"),
        }
        for supply in all_supplies
        if supply["status"] == Status.CATCHING.value
    ]

    # Имя клиента
    client = await orm_controller.get_client_by_id(client_id)
    client_name = client.name if client else "❓ Неизвестно"

    return {"tasks": catching_tasks, "selected_client_name": client_name}

async def on_name_entered(message: types.Message, manager, value: str):
    client_id = manager.dialog_data.get("selected_client")
    new_name = value
    result = await orm_controller.update_client_name(client_id, new_name)

    await message.answer(result.get("message", result.get("error", "❌ Ошибка при обновлении имени")))
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.DELETE_AND_SEND)

async def on_cookies_entered(message: types.Message, manager, value: str):
    client_id = manager.dialog_data.get("selected_client")
    new_cookies = value
    result = await orm_controller.update_client_cookies(client_id, new_cookies)

    await message.answer(result.get("message", result.get("error", "❌ Ошибка при обновлении cookies")))
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.DELETE_AND_SEND)

task_dialog = Dialog(
    Window(
        Jinja(
            "{% if no_clients %}❌ У вас пока нет кабинетов. Добавьте первый, нажав на кнопку ниже.\n\n"
            "{% else %}👥 <b>Выберите кабинет:</b>\n\n"
            "{% for client in clients %}🔹 <b>{{ client[0] }}</b> (ID: {{ client[1] }})\n{% endfor %}{% endif %}"
        ),
        Select(
            text=Format("{item[0]}"),
            id="select_supply",
            item_id_getter=operator.itemgetter(1),
            items="clients",  # ← теперь ключ совпадает
            on_click=on_client_selected,
        ),
        Button(
            Jinja("➕ Добавить кабинет"),
            id="add_client",
            on_click=on_add_client,
            when=lambda data, w, m: data.get("no_clients", False)  # Показываем кнопку, если нет кабинетов
        ),
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.start(state=MainMenu.MAIN_MENU, show_mode=ShowMode.EDIT)),
        state=ManageClientStates.CHOOSE_CLIENT,
        getter=get_clients_list,
        parse_mode="HTML",
    ),
    Window(
        Jinja(
            "🔹 <b>Выбран кабинет:</b> {{ selected_client_name }}\n\n"
            "Выберите действие:"
        ),
        Button(Jinja("📦 Поставки клиента"), id="client_supplies",
               on_click=lambda c, w, m: m.switch_to(ManageClientStates.CLIENT_SUPPLIES, show_mode=ShowMode.EDIT)),
        Button(
            Jinja("🎯 Актуальные отловы"),
            id="active_tasks",
            on_click=lambda c, w, m: m.switch_to(ManageClientStates.ACTIVE_TASKS),
        ),
        Button(Jinja("🔄 Обновить данные"), id="update_client",
               on_click=lambda c, w, m: m.switch_to(ManageClientStates.UPDATE_CLIENT)),
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.back(show_mode=ShowMode.EDIT)),
        state=ManageClientStates.CHOOSE_ACTION,
        getter=get_selected_client,  # ✅ добавили
        parse_mode="HTML",
    ),
    Window(
        List(
            Format("{item}"),
            items='supply_details',
            id="TEXT_SCROLL",
            page_size=5,
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="select_supply",
                item_id_getter=operator.itemgetter(0),
                items="supplies",
                on_click=on_supply_selected,
            ),
            id="supply_pagination",
            width=1,
            height=5,
            on_page_changed=sync_scroll('TEXT_SCROLL'),  # Синхронизация страниц
        ),

        Button(
            Jinja("🔙 Назад"),
            id="back",
            on_click=lambda c, w, m: on_back_pressed(m),
        ),
        state=ManageClientStates.CLIENT_SUPPLIES,
        getter=get_supplies_list,
        parse_mode="HTML",
    ),
    Window(
        List(
            Format("{item}"),
            items="supply_details",  # 👈 список строк с инфой по каждой активной поставке
            id="ACTIVE_SCROLL_TEXT",
            page_size=5,
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="active_supply_select",
                item_id_getter=operator.itemgetter(0),
                items="supplies",  # 👈 список кортежей: (supply_id, supply_id)
                on_click=on_supply_selected,
            ),
            id="active_supply_scroll",
            width=1,
            height=5,
            on_page_changed=sync_scroll("ACTIVE_SCROLL_TEXT"),
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, w, m: m.switch_to(state=ManageClientStates.CHOOSE_ACTION,show_mode=ShowMode.EDIT),
        ),
        state=ManageClientStates.ACTIVE_TASKS,
        getter=get_active_catching_tasks,  # 👈 твоя функция, которая вернет нужный формат данных
        parse_mode="HTML",
    ),
    Window(
        Jinja("🛠 Что вы хотите обновить для кабинета {{ selected_client_name }}?"),

        Button(Const("✏️ Изменить имя"), id="edit_name", on_click=lambda c, w, m: m.switch_to
        (state=ManageClientStates.ENTER_NEW_NAME, show_mode=ShowMode.EDIT)),

        Button(Const("🔐 Обновить cookies"), id="edit_cookies", on_click=lambda c, w, m: m.switch_to
        (state=ManageClientStates.ENTER_NEW_COOKIES, show_mode=ShowMode.EDIT)),

        Button(Const("🔙 Назад"), id="back_from_update", on_click=lambda c, w, m: m.switch_to
        (state=ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.EDIT)),

        state=ManageClientStates.UPDATE_CLIENT,
        getter=get_selected_client,
    ),
    Window(
        Const("✏️ Введите новое имя клиента:"),
        TextInput(
            id="new_name_input",
            on_success=lambda m, w, manager, value: on_name_entered(m, manager, value)
        ),
        Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to
        (state=ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.EDIT)),
        state=ManageClientStates.ENTER_NEW_NAME,
    ),
    Window(
        Const("🔐 Вставьте новые cookies для клиента:"),
        TextInput(
            id="new_cookies_input",
            on_success=lambda m, w, manager, value: on_cookies_entered(m, manager, value)
        ),
        Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to
        (state=ManageClientStates.CHOOSE_ACTION, show_mode=ShowMode.EDIT)),
        state=ManageClientStates.ENTER_NEW_COOKIES,
    )
)
