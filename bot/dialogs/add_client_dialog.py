import logging
import operator

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Row, Column, Multiselect
from aiogram_dialog.widgets.text import Jinja, Const, Format
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery

from bot.utils.statesform import AddClientStates, MainMenu
from database.controller.ORM import ORMController
from bot.utils.wildberries_api import WildberriesAPI
from bot.utils.validations import normalize_phone_number

orm_controller = ORMController()
logger = logging.getLogger(__name__)

#____________________________
async def on_phone_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    phone: str,
):
    phone = normalize_phone_number(phone)
    logger.info(f"📞 Введён номер телефона: {phone}")
    dialog_manager.dialog_data["phone_number"] = phone
    logger.info("📡 Отправка запроса на получение SMS-кода...")

    try:
        api = WildberriesAPI(phone_number=phone)
        success, error_msg = api.send_code()
        if success:
            dialog_manager.dialog_data["phone_number"] = phone
            dialog_manager.dialog_data["sticker"] = api.sticker  # 🔥 сохраняем только sticker
            await dialog_manager.switch_to(AddClientStates.ENTER_SMS_CODE)
        else:
            logger.warning(f"⚠️ Не удалось отправить код: {error_msg}")
            await message.answer(error_msg)
    except Exception as e:
        logger.exception("❌ Ошибка при отправке SMS-кода")
        await message.answer(f"❌ Ошибка при отправке кода: {str(e)}")

async def on_phone_error(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    error: ValueError,
):
    logger.warning("🚫 Ошибка валидации номера телефона")
    await message.answer("⚠️ Введите корректный номер телефона в формате +79991234567")

async def on_sms_code_entered(
        message: Message,
        widget: ManagedTextInput[str],
        dialog_manager: DialogManager,
        code: str):
    logger.info(f"📨 Введён SMS-код: {code}")

    phone = dialog_manager.dialog_data.get("phone_number")
    sticker = dialog_manager.dialog_data.get("sticker")

    if not phone or not sticker:
        await message.answer("⚠️ Ошибка: данные утеряны. Попробуйте сначала.")
        return

    api = WildberriesAPI(phone_number=phone)
    api.sticker = sticker

    try:
        result = api.authorize(code)

        cookies_dict = result["cookies"]
        access_token = result["json"]["payload"]["access_token"]
        validation_key = result["wbx_validation_key"]

        # Собираем куки строкой
        cookie_string = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())

        # Добавим вручную wbx-validation-key, если он не попал в session.cookies
        if validation_key and "wbx-validation-key" not in cookies_dict:
            cookie_string += f"; {validation_key}"

        # Сохраняем
        dialog_manager.dialog_data["auth_response"] = {
            "cookie_string": cookie_string,
            "access_token": access_token
        }

        await dialog_manager.switch_to(AddClientStates.SELECT_CLIENTS, show_mode=ShowMode.EDIT)
    except Exception as e:
        logger.exception("❌ Ошибка авторизации")
        await message.answer(f"❌ Ошибка авторизации: {str(e)}")


async def on_sms_code_error(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    error: ValueError,
):
    logger.warning("🚫 Ошибка ввода авторизационного кода")
    await message.answer("⚠️ Ошибка кода, попробуйте еще раз")
    await dialog_manager.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.DELETE_AND_SEND)

async def get_suppliers_data(dialog_manager: DialogManager, **kwargs):
    # Предположим, что результат запроса к API уже сохранён в dialog_manager или передаётся через kwargs
    raw_data = dialog_manager.dialog_data.get("raw_suppliers_response")

    suppliers_raw = raw_data[0]["result"]["suppliers"]
    suppliers = [(supplier["name"], supplier["id"]) for supplier in suppliers_raw]

    return {
        "suppliers": suppliers,
        "count": len(suppliers),
    }

async def on_add_selected(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_ids = await manager.find("m_suppliers").get_checked()
    logger.info(f"📦 Выбранные поставщики: {selected_ids}")
    #TODO: Зарегистрируй всех поставщиков в БД
    await manager.done()

async def on_add_all(callback: CallbackQuery, button: Button, manager: DialogManager):
    suppliers = manager.dialog_data.get("suppliers_data", [])
    all_ids = [str(s[1]) for s in suppliers]
    logger.info(f"📦 Добавлены ВСЕ поставщики: {all_ids}")
    #TODO: Зарегистрируй всех поставщиков в БД
    await manager.done()

add_client_dialog = Dialog(
    Window(
        Jinja(
            "👋 <b>Добавление новых клиентов</b>\n\n"
            "🔐 Регистрация происходит через номер телефона. "
            "Вы введёте свой номер, получите SMS-код от Wildberries, а затем выберете кабинеты для регистрации из списка доступных.\n\n"
            "📲 <b>Готовы начать?</b>"
        ),
        Column(
            Button(Const("➡️ Начать"), id="start_phone_flow",
                   on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_PHONE)),
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        ),
        state=AddClientStates.ENTRY_METHOD,
        parse_mode="HTML",
    ),
    Window(
        Const("📞 <b>Введите номер телефона:</b>\n"
              "<code>+79991234567</code>\n"
              "📩 <i>Мы отправим на него код подтверждения</i>"),
        TextInput(
            id="phone_number",
            type_factory=str,  # можно заменить на кастомный валидатор
            on_success=on_phone_entered,
            on_error=on_phone_error,
        ),
        Row(
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTRY_METHOD)),
        ),
        state=AddClientStates.ENTER_PHONE,
        parse_mode="HTML",
    ),
    Window(
        Jinja(
            "📲 <b>Введите код из SMS от WildBerries для получения списка доступных клиентов</b>\n\n"
        ),
        TextInput(
            id="sms_code",
            type_factory=str,
            on_success=on_sms_code_entered,
            on_error=on_sms_code_error,
        ),
        Row(
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_PHONE)),
        ),
        state=AddClientStates.ENTER_SMS_CODE,
        parse_mode="HTML",
    ),
    Window(
        Const("📦 Выберите поставщиков из списка ниже или нажмите 'Добавить всех'"),
        Multiselect(
            checked_text=Format("✓ {item[0]}"),
            unchecked_text=Format("{item[0]}"),
            id="m_suppliers",
            item_id_getter=operator.itemgetter(1),  # берем item[1] как ID
            items="suppliers",  # это ключ из data, получаемого в get_data
        ),
        Row(
            Button(Const("✅ Добавить выбранных"), id="add_selected", on_click=on_add_selected),
            Button(Const("📋 Добавить всех"), id="add_all", on_click=on_add_all),
        ),
        Row(
            Button(Const("🔙 В главное меню"), id="to_main", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        ),
        state=AddClientStates.SELECT_CLIENTS,
        getter=get_suppliers_data,
        parse_mode="HTML",
    )
)
