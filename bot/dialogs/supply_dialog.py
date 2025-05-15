from datetime import date

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Select, Button, ScrollingGroup, Back, Calendar
from aiogram_dialog.widgets.text import Jinja, Format, Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery

from database.controller.orm_instance import get_orm
from bot.utils.statesform import SupplyStates
from database.enums import Status
from services.utils.logger import setup_logger
from services.utils.mpwave_api import MPWAVEAPI

logger = setup_logger(__name__)
mpwave_api = MPWAVEAPI()
orm_controller = get_orm()

PAGE_SIZE = 5  # Количество поставок на одной странице

async def on_action_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    if item_id == "cancel":
        await cancel_catch(manager)
    elif item_id == "edit":
        await manager.switch_to(SupplyStates.CHOOSE_COEFFICIENT, show_mode=ShowMode.EDIT)
    else:
        await manager.switch_to(SupplyStates.CHOOSE_COEFFICIENT, show_mode=ShowMode.EDIT)

async def cancel_catch(manager: DialogManager):
    """Обработчик отмены отлова"""
    supply_id = int(manager.dialog_data["selected_supply"])
    client_id = manager.dialog_data["selected_client"]
    manager.dialog_data["force_reload"] = True

    #TODO: Отправить запрос на отмену поставки через MPWAVE_API и обработать ответ

    await mpwave_api.cancel_task_api(client_id, supply_id)

    # result = await orm_controller.cancel_catching(client_id=client_id, supply_id=supply_id)
    #
    # if "error" in result:
    #     await manager.event.message.answer(f"❌ {result['error']}")
    # else:
    #     await manager.event.message.answer(f"✅ {result['message']}")

    # Очистка временных данных
    for key in ("selected_supply", "start_date", "end_date", "skip_dates", "coefficient", "is_catching"):
        manager.dialog_data.pop(key, None)

    # Возврат в список поставок
    manager.dialog_data["force_reload"] = True
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)

async def get_supply_options(dialog_manager: DialogManager, **kwargs):
    supply_id = dialog_manager.start_data.get("supply_id")
    client_id = dialog_manager.start_data.get("client_id")

    # Сохраняем в dialog_data для последующего использования
    dialog_manager.dialog_data["selected_supply"] = supply_id
    dialog_manager.dialog_data["selected_client"] = client_id

    # Получаем статус из базы данных
    supply = await orm_controller.supply.get_supply_by_id(supply_id)
    is_catching = False
    if supply:
        is_catching = supply.status == Status.CATCHING
        dialog_manager.dialog_data["is_catching"] = is_catching

    logger.info(f"Получение опций для поставки {supply_id}. Статус is_catching: {is_catching}")

    buttons = []
    if is_catching:
        buttons.append(("❌ Отменить отлов", "cancel"))
        buttons.append(("✏️ Изменить параметры", "edit"))
    else:
        buttons.append(("📌 Взять на отлов", "catch"))

    return {"options": buttons, "supply_id": supply_id}

async def on_coefficient_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["coefficient"] = int(item_id)
    await manager.switch_to(SupplyStates.CHOOSE_START_DATE, show_mode=ShowMode.EDIT)
    
async def on_date_selected(callback: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    state = manager.current_context().state
    selected_str = selected_date.strftime("%Y-%m-%d")

    if state == SupplyStates.CHOOSE_START_DATE:
        manager.dialog_data["start_date"] = selected_str
        await manager.switch_to(SupplyStates.CHOOSE_END_DATE, show_mode=ShowMode.EDIT)

    elif state == SupplyStates.CHOOSE_END_DATE:
        manager.dialog_data["end_date"] = selected_str
        await manager.switch_to(SupplyStates.CHOOSE_SKIP_DATES, show_mode=ShowMode.EDIT)

    elif state == SupplyStates.CHOOSE_SKIP_DATES:
        skip_dates = manager.dialog_data.get("skip_dates", [])
        if selected_str in skip_dates:
            skip_dates.remove(selected_str)
        else:
            skip_dates.append(selected_str)
        manager.dialog_data["skip_dates"] = skip_dates

        # Обновим окно, чтобы текст `{skip_dates}` отобразился актуальным
        await manager.show()
        
async def get_start_date(dialog_manager: DialogManager, **kwargs):
    return {"start_date": dialog_manager.dialog_data.get("start_date", "не выбрана")}

async def get_end_date(dialog_manager: DialogManager, **kwargs):
    return {"end_date": dialog_manager.dialog_data.get("end_date", "не выбрана")}

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

    #TODO: Отправить запрос на MPWAVE_API о начале отлова и обратать ответ сервера
    data = {
        "supply_id": supply_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "skip_dates": [d.isoformat() for d in skip_dates],
        "coefficient": coefficient
    }

    await mpwave_api.start_task_api(data)

    # result = await orm_controller.confirm_supply_catching(
    #     supply_id=supply_id,
    #     start_date=start_date,
    #     end_date=end_date,
    #     skip_dates=skip_dates,
    #     coefficient=coefficient
    # )

    # if "error" in result:
    #     await callback.message.answer(f"❌ {result['error']}")
    # else:
    #     await callback.message.answer(f"✅ {result['message']}")

    # Очистка временных данных
    for key in ("selected_supply", "start_date", "end_date", "skip_dates", "coefficient", "is_catching"):
        manager.dialog_data.pop(key, None)

    manager.dialog_data["force_reload"] = True
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)
    
async def get_confirm_data(dialog_manager: DialogManager, **kwargs):
    return {
        "supply_id": dialog_manager.dialog_data.get("selected_supply", "❌"),
        "start_date": dialog_manager.dialog_data.get("start_date", "❌"),
        "end_date": dialog_manager.dialog_data.get("end_date", "❌"),
        "coefficient": dialog_manager.dialog_data.get("coefficient", "❌"),
        "skip_dates": ", ".join(dialog_manager.dialog_data.get("skip_dates", [])) or "—"
    }

supply_dialog = Dialog(
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
            on_click=lambda c, b, d: d.done(show_mode=ShowMode.EDIT),
        ),
        state=SupplyStates.CHOOSE_SUPPLY_ACTION,
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
        state=SupplyStates.CHOOSE_COEFFICIENT,
    ),
    Window(
        Format("Выберите дату начала: Текущая: {start_date}"),
        Calendar(id="start_date", on_click=on_date_selected),
        Back(Const("🔙 Назад")),
        state=SupplyStates.CHOOSE_START_DATE,
        getter=get_start_date,  # ✅ Используем исправленный getter
    ),
    Window(
        Format("Выберите дату окончания: Текущая: {end_date}"),
        Calendar(id="end_date", on_click=on_date_selected),
        Back(Const("🔙 Назад")),
        state=SupplyStates.CHOOSE_END_DATE,
        getter=get_end_date,  # ✅ Используем исправленный getter
    ),
    Window(
        Format("Выберите даты, которые необходимо пропустить: Текущие: {skip_dates}"),
        Calendar(id="skip_dates", on_click=on_date_selected),
        Button(Const("⏭ Подтвердить"), id="skip", on_click=lambda c, b, d: d.switch_to(SupplyStates.CONFIRM, show_mode=ShowMode.EDIT)),
        Back(Const("🔙 Назад")),
        state=SupplyStates.CHOOSE_SKIP_DATES,
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
        state=SupplyStates.CONFIRM,
        getter=get_confirm_data,
        parse_mode="HTML",
    )
)