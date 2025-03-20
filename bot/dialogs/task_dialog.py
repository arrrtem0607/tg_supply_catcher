import operator
import logging

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button, ScrollingGroup
from aiogram_dialog.widgets.text import Jinja, List, Format
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database.controller.ORM import ORMController
from bot.utils.statesform import ManageClientStates, MainMenu, AddClientStates
from bot.utils.castom_scroll import sync_scroll, ManagedScroll

logger = logging.getLogger(__name__)

orm_controller = ORMController()

PAGE_SIZE = 5  # Количество поставок на одной странице

# Словарь для перевода статусов на русский язык
STATUS_TRANSLATION = {
    "RECEIVED": "📥 Получено",
    "CATCHING": "🎯 Ловится",
    "CAUGHT": "✅ Поймано",
    "ERROR": "❌ Ошибка",
    "CANCELLED": "🚫 Отменено",
    "PLANNED": "📌 Запланировано",
    "IN_PROGRESS": "⏳ В процессе",
    "COMPLETED": "✅ Завершено",
}

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
    manager.dialog_data["selected_client"] = item_id
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION)

async def on_my_clients(callback: CallbackQuery, widget, manager: DialogManager):
    """Открываем список кабинетов пользователя"""
    await manager.start(ManageClientStates.CHOOSE_CLIENT)

async def get_supplies_list(dialog_manager: DialogManager, **kwargs):
    """Загружает ВСЕ поставки пользователя, кэширует их и формирует первую страницу"""
    tg_id = dialog_manager.event.from_user.id
    client_id = dialog_manager.dialog_data.get("selected_client")

    if not client_id:
        return {"supplies": [], "supply_details": "❌ Нет данных по поставкам"}

    # ✅ Загружаем ВСЕ поставки из БД
    if "cached_supplies" not in dialog_manager.dialog_data:
        db_supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)

        if not db_supplies:
            return {
                "supplies": [],
                "supply_details": "📦 Нет доступных поставок"
            }

        # ✅ Кешируем поставки
        db_supplies = sorted(db_supplies, key=lambda x: x.get("api_created_at", ""), reverse=True)
        dialog_manager.dialog_data["cached_supplies"] = db_supplies
        dialog_manager.dialog_data["supply_pagination"] = 0  # Начальная страница

    # ✅ Формируем первую страницу
    db_supplies = dialog_manager.dialog_data["cached_supplies"]
    first_page_supplies = db_supplies[:1000]  # Ограничим страницу 5 элементами

    supply_list = []
    supply_text_list = []

    for supply in first_page_supplies:
        supply_id = str(supply.get("id", "❌ Без ID"))
        warehouse_name = supply.get("warehouse_name", "❌ Неизвестный склад")
        box_type = supply.get("box_type", "❌ Неизвестный тип")

        # Перевод статуса на русский
        status = supply.get("status", "❌ Неизвестный статус")
        status_rus = STATUS_TRANSLATION.get(status, status)

        supply_list.append(supply_id)
        supply_text_list.append(
            f"🔹 <b>Поставка {supply_id}</b>\n"
            f"🏬 Склад: {warehouse_name}\n"
            f"📦 Тип: {box_type}\n"
            f"📌 Статус: {status_rus}\n"
        )

    # ✅ Гарантируем, что текст не пустой
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

async def on_supply_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора поставки"""
    manager.dialog_data["selected_supply"] = item_id
    await manager.switch_to(ManageClientStates.SUPPLY_ACTIONS)

async def on_add_client(callback: CallbackQuery, widget, manager: DialogManager):
    """Обработчик кнопки добавления кабинета"""
    await manager.start(AddClientStates.ENTER_NAME)

async def on_back_pressed(manager: DialogManager):
    """Удаляет только кешированные поставки и возвращает в главное меню"""
    manager.dialog_data.pop("cached_supplies", None)  # Удаляем только кэш поставок, если он есть
    manager.dialog_data.pop("supply_pagination", None)  # Также сбрасываем номер страницы
    await manager.switch_to(ManageClientStates.CHOOSE_ACTION)  # Возвращаем в главное меню


task_dialog = Dialog(
    Window(
        Jinja(
            "{% if no_clients %}❌ У вас пока нет кабинетов. Добавьте первый, нажав на кнопку ниже.\n\n"
            "{% else %}👥 <b>Выберите кабинет:</b>\n\n"
            "{% for client in clients %}🔹 <b>{{ client[0] }}</b> (ID: {{ client[1] }})\n{% endfor %}{% endif %}"
        ),
        Select(
            text=Jinja("🔹 {{ item[0] }}"),
            id="select_client",
            item_id_getter=operator.itemgetter(1),
            items="clients",
            on_click=on_client_selected,
            when=lambda data, w, m: not data.get("no_clients", False)  # Скрываем кнопку, если кабинетов нет
        ),
        Button(
            Jinja("➕ Добавить кабинет"),
            id="add_client",
            on_click=on_add_client,
            when=lambda data, w, m: data.get("no_clients", False)  # Показываем кнопку, если нет кабинетов
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
        List(
            Format("{item}"),
            items='supply_details',
            id="TEXT_SCROLL",
            page_size=5,
        ),
        ScrollingGroup(
            Select(
                Format("{item}"),
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
    )
)
