import operator
import logging
from datetime import date
import aiohttp

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Select, Button, ScrollingGroup, Back, Calendar
from aiogram_dialog.widgets.text import Jinja, List, Format, Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from database.controller.ORM import ORMController
from bot.utils.statesform import ManageClientStates, MainMenu, AddClientStates
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
    await manager.start(ManageClientStates.CHOOSE_CLIENT)

async def get_supplies_list(dialog_manager: DialogManager, **kwargs):
    tg_id = dialog_manager.event.from_user.id
    client_id = dialog_manager.dialog_data.get("selected_client")

    logger.info(f"Загружаем поставки для пользователя {tg_id}, client_id: {client_id}")

    if not client_id:
        logger.warning("Нет выбранного client_id. Возвращаем пустые данные.")
        return {"supplies": [], "supply_details": []}  # supply_details → список строк

    # Принудительное обновление
    force_reload = dialog_manager.dialog_data.pop("force_reload", False)
    if force_reload or "cached_supplies" not in dialog_manager.dialog_data:
        db_supplies = await orm_controller.get_supplies_by_client(tg_id, client_id)

        if not db_supplies:
            logger.warning(f"Поставки для клиента {client_id} не найдены.")
            return {
                "supplies": [],
                "supply_details": []
            }

        db_supplies = sorted(db_supplies, key=lambda x: x.get("api_created_at", ""), reverse=True)
        dialog_manager.dialog_data["cached_supplies"] = db_supplies
        dialog_manager.dialog_data["supply_pagination"] = 0
        logger.info(f"Кешировано {len(db_supplies)} поставок для клиента {client_id}")

    # Формируем страницу из кеша
    db_supplies = dialog_manager.dialog_data["cached_supplies"]
    first_page_supplies = db_supplies[:1000]

    supply_list = []
    supply_text_list = []

    for supply in first_page_supplies:
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
    await manager.start(AddClientStates.ENTER_NAME)

async def on_back_pressed(manager: DialogManager):
    """Удаляет только кешированные поставки и возвращает в главное меню"""
    manager.dialog_data.pop("cached_supplies", None)  # Удаляем только кэш поставок, если он есть
    manager.dialog_data.pop("supply_pagination", None)  # Также сбрасываем номер страницы
    await manager.back(show_mode=ShowMode.EDIT)  # Возвращаем в главное меню

async def on_back_to_previous(callback, button, manager: DialogManager):
    print(manager.current_stack())
    print(manager.current_context())
    stack = await manager.current_stack().stack()  # получаем список состояний
    if len(stack) >= 2:
        previous_state = stack[-2].state
        await manager.switch_to(previous_state, show_mode=ShowMode.EDIT)
    else:
        from bot.utils.statesform import MainMenu
        await manager.switch_to(MainMenu.MAIN_MENU, show_mode=ShowMode.EDIT)

async def get_supply_options(dialog_manager: DialogManager, **kwargs):
    supply_id = dialog_manager.dialog_data.get("selected_supply")
    is_catching = dialog_manager.dialog_data.get("is_catching", False)

    logger.info(f"Получение опций для поставки {supply_id}. Статус is_catching: {is_catching}")

    buttons = []
    if is_catching:
        buttons.append(("❌ Отменить отлов", "cancel"))
        buttons.append(("✏️ Изменить параметры", "edit"))
    else:
        buttons.append(("📌 Взять на отлов", "catch"))

    logger.info(f"Кнопки для отображения: {buttons}")
    return {"options": buttons, "supply_id": supply_id}

async def on_supply_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработчик выбора поставки."""
    logger.info(f"Выбор поставки: {item_id}")

    # Сохраняем выбранный supply_id в диалоговых данных
    manager.dialog_data["selected_supply"] = item_id
    logger.info(f"Сохранен supply_id в dialog_data: {item_id}")

    # Получаем статус поставки из базы данных
    supply = await orm_controller.get_supply_by_id(item_id)
    if supply:
        # Обновляем состояние в диалоговых данных на основе статуса из базы данных
        is_catching = (supply.status == Status.CATCHING)  # Используем Enum Status для проверки
        manager.dialog_data["is_catching"] = is_catching

        logger.info(
            f"Статус поставки {item_id}: {Status.get_translation(supply.status)}. Состояние is_catching обновлено на {manager.dialog_data['is_catching']}")
    else:
        # Если поставка не найдена, оставляем значение по умолчанию
        manager.dialog_data["is_catching"] = False
        logger.warning(f"Поставка с ID {item_id} не найдена. Состояние is_catching установлено в False.")

    # Переключаем на следующий экран
    logger.info(f"Переключение на экран {ManageClientStates.CHOOSE_SUPPLY_ACTION}")
    await manager.switch_to(ManageClientStates.CHOOSE_SUPPLY_ACTION, show_mode=ShowMode.EDIT)

async def on_action_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    if item_id == "cancel":
        await cancel_catch(manager)
    elif item_id == "edit":
        await manager.switch_to(ManageClientStates.CHOOSE_COEFFICIENT, show_mode=ShowMode.EDIT)
    else:
        await manager.switch_to(ManageClientStates.CHOOSE_COEFFICIENT, show_mode=ShowMode.EDIT)

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

async def on_coefficient_input(message, widget, manager: DialogManager, value: str):
    try:
        manager.dialog_data["coefficient"] = int(value)

        # ✅ Добавляем `start_date`, если его нет
        if "start_date" not in manager.dialog_data:
            manager.dialog_data["start_date"] = None

        await manager.switch_to(ManageClientStates.CHOOSE_START_DATE, show_mode=ShowMode.EDIT)
    except ValueError:
        await message.answer("Введите число!")

async def on_coefficient_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["coefficient"] = int(item_id)
    await manager.switch_to(ManageClientStates.CHOOSE_START_DATE, show_mode=ShowMode.EDIT)

async def get_start_date(dialog_manager: DialogManager, **kwargs):
    return {"start_date": dialog_manager.dialog_data.get("start_date", "не выбрана")}

async def get_end_date(dialog_manager: DialogManager, **kwargs):
    return {"end_date": dialog_manager.dialog_data.get("end_date", "не выбрана")}

async def on_date_selected(callback: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    state = manager.current_context().state
    selected_str = selected_date.strftime("%Y-%m-%d")

    if state == ManageClientStates.CHOOSE_START_DATE:
        manager.dialog_data["start_date"] = selected_str
        await manager.switch_to(ManageClientStates.CHOOSE_END_DATE, show_mode=ShowMode.EDIT)

    elif state == ManageClientStates.CHOOSE_END_DATE:
        manager.dialog_data["end_date"] = selected_str
        await manager.switch_to(ManageClientStates.CHOOSE_SKIP_DATES, show_mode=ShowMode.EDIT)

    elif state == ManageClientStates.CHOOSE_SKIP_DATES:
        skip_dates = manager.dialog_data.get("skip_dates", [])
        if selected_str in skip_dates:
            skip_dates.remove(selected_str)
        else:
            skip_dates.append(selected_str)
        manager.dialog_data["skip_dates"] = skip_dates

        # Обновим окно, чтобы текст `{skip_dates}` отобразился актуальным
        await manager.show()

async def get_skip_dates(dialog_manager: DialogManager, **kwargs):
    """Возвращает текущие даты пропуска, если их нет - создает пустой список"""
    return {"skip_dates": dialog_manager.dialog_data.get("skip_dates", [])}

async def on_confirm(callback: CallbackQuery, button, manager: DialogManager):
    """Обработчик подтверждения отлова"""
    supply_id = int(manager.dialog_data["selected_supply"])
    start_date = manager.dialog_data["start_date"]
    end_date = manager.dialog_data["end_date"]
    skip_dates = manager.dialog_data.get("skip_dates", [])
    coefficient = manager.dialog_data["coefficient"]
    manager.dialog_data["force_reload"] = True

    result = await orm_controller.confirm_supply_catching(
        supply_id=supply_id,
        start_date=start_date,
        end_date=end_date,
        skip_dates=skip_dates,
        coefficient=coefficient
    )

    if "error" in result:
        await callback.message.answer(f"❌ {result['error']}")
    else:
        await callback.message.answer(f"✅ {result['message']}")

    # Очистка временных данных
    for key in ("selected_supply", "start_date", "end_date", "skip_dates", "coefficient", "is_catching"):
        manager.dialog_data.pop(key, None)

    # Возврат в список поставок
    await manager.switch_to(ManageClientStates.CLIENT_SUPPLIES, show_mode=ShowMode.DELETE_AND_SEND)

async def get_confirm_data(dialog_manager: DialogManager, **kwargs):
    return {
        "supply_id": dialog_manager.dialog_data.get("selected_supply", "❌"),
        "start_date": dialog_manager.dialog_data.get("start_date", "❌"),
        "end_date": dialog_manager.dialog_data.get("end_date", "❌"),
        "coefficient": dialog_manager.dialog_data.get("coefficient", "❌"),
        "skip_dates": ", ".join(dialog_manager.dialog_data.get("skip_dates", [])) or "—"
    }

async def cancel_supply_task(manager: DialogManager):
    """Отправляет запрос на отмену поставки через API"""
    supply_id = int(manager.dialog_data["selected_supply"])
    client_id = manager.dialog_data["selected_client"]  # UUID как строка

    data = {
        "client_id": client_id,
        "preorder_id": supply_id,
    }

    logger.info(f"⛔ Отмена поставки {supply_id} для клиента {client_id}")

    async with aiohttp.ClientSession() as session:
        async with session.post("http://127.0.0.1:8001/catcher/cancel_task", json=data) as resp:
            response_text = await resp.text()
            if resp.status == 200:
                await manager.event.message.answer(f"🗑 Поставка {supply_id} отменена.")
            else:
                await manager.event.message.answer(f"❌ Ошибка при отмене поставки: {response_text}")

    # Очистка кеша поставок и возврат
    manager.dialog_data.pop("cached_supplies", None)
    manager.dialog_data.pop("supply_pagination", None)
    await manager.switch_to(ManageClientStates.CLIENT_SUPPLIES, show_mode=ShowMode.EDIT)

async def cancel_catch(manager: DialogManager):
    """Обработчик отмены отлова"""
    supply_id = int(manager.dialog_data["selected_supply"])
    client_id = manager.dialog_data["selected_client"]
    manager.dialog_data["force_reload"] = True

    result = await orm_controller.cancel_catching(client_id=client_id, supply_id=supply_id)

    if "error" in result:
        await manager.event.message.answer(f"❌ {result['error']}")
    else:
        await manager.event.message.answer(f"✅ {result['message']}")

    # Очистка временных данных
    for key in ("selected_supply", "start_date", "end_date", "skip_dates", "coefficient", "is_catching"):
        manager.dialog_data.pop(key, None)

    # Возврат в список поставок
    await manager.switch_to(ManageClientStates.CLIENT_SUPPLIES, show_mode=ShowMode.DELETE_AND_SEND)


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
        Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU, show_mode=ShowMode.EDIT)),
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
        Format("Выберите действие для поставки {supply_id}:"),
        Select(
            text=Format("{item[0]}"),
            items="options",
            id="supply_action",
            item_id_getter=lambda x: x[1],
            on_click=on_action_selected,
        ),
        Button(
            Jinja("🔙 Назад"),
            id="back",
            on_click=on_back_to_previous,
        ),
        state=ManageClientStates.CHOOSE_SUPPLY_ACTION,
        getter=get_supply_options,
    ),
    Window(
        Const("Выберите максимальный коэффициент для отлова.\n\n"
              "Бот будет ловить все коэффициенты включительно ниже выбранного:"),
        # 🔘 Кнопки выбора коэффициента (0-20)
        ScrollingGroup(
            Select(
                text=Format("{item}"),
                id="select_coefficient",
                item_id_getter=lambda x: str(x),
                items=list(range(0, 21)),
                on_click=on_coefficient_selected,
            ),
            id="coefficient_scroll",
            width=5,  # ✅ 5 кнопок в ряд
            height=4,  # ✅ 4 строки (всего 20 кнопок)
        ),

        Back(Const("🔙 Назад")),
        state=ManageClientStates.CHOOSE_COEFFICIENT,
    ),
    Window(
        Format("Выберите дату начала: Текущая: {start_date}"),
        Calendar(id="start_date", on_click=on_date_selected),
        Back(Const("🔙 Назад")),
        state=ManageClientStates.CHOOSE_START_DATE,
        getter=get_start_date,  # ✅ Используем исправленный getter
    ),
    Window(
        Format("Выберите дату окончания: Текущая: {end_date}"),
        Calendar(id="end_date", on_click=on_date_selected),
        Back(Const("🔙 Назад")),
        state=ManageClientStates.CHOOSE_END_DATE,
        getter=get_end_date,  # ✅ Используем исправленный getter
    ),
    Window(
        Format("Выберите даты, которые необходимо пропустить: Текущие: {skip_dates}"),
        Calendar(id="skip_dates", on_click=on_date_selected),
        Button(Const("⏭ Подтвердить"), id="skip", on_click=lambda c, b, d: d.switch_to(ManageClientStates.CONFIRM, show_mode=ShowMode.EDIT)),
        Back(Const("🔙 Назад")),
        state=ManageClientStates.CHOOSE_SKIP_DATES,
        getter=get_skip_dates,  # ✅ Теперь всегда передаем skip_dates, даже если список пуст
    ),
    Window(
        Jinja(
            "<b>📋 Подтвердите данные:</b>\n\n"
            "🆔 Поставка: <code>{{ supply_id }}</code>\n"
            "⚙️ Коэффициент: <b>{{ coefficient }}</b>\n"
            "📅 Дата начала: <b>{{ start_date }}</b>\n"
            "📅 Дата окончания: <b>{{ end_date }}</b>\n"
            "⛔ Пропущенные даты: <b>{{ skip_dates }}</b>\n\n"
            "❓ Всё верно?"
        ),
        Button(Const("✅ Подтвердить"), id="confirm", on_click=on_confirm),
        Back(Const("🔙 Назад")),
        state=ManageClientStates.CONFIRM,
        getter=get_confirm_data,
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
            on_click=lambda c, w, m: m.back(show_mode=ShowMode.EDIT),
        ),
        state=ManageClientStates.ACTIVE_TASKS,
        getter=get_active_catching_tasks,  # 👈 твоя функция, которая вернет нужный формат данных
        parse_mode="HTML",
    ),
)
