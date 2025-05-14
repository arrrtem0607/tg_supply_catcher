import operator
import aiohttp
import requests

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Row, Column, Multiselect, ScrollingGroup, ManagedMultiselect
from aiogram_dialog.widgets.text import Jinja, Const, Format
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery

from bot.utils.statesform import AddClientStates, MainMenu
from bot.utils.validations import normalize_phone_number
from services.utils.logger import setup_logger

BACKEND_URL = "https://waveapitest.ru"
logger = setup_logger(__name__)

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
        res = requests.post(url=BACKEND_URL + "/catcher/send_code", params={'phone_number': phone})
        if res.status_code == 200:
            dialog_manager.dialog_data["phone_number"] = phone
            dialog_manager.dialog_data["sticker"] = res.json()["payload"]['sticker']
            await dialog_manager.switch_to(AddClientStates.ENTER_SMS_CODE, show_mode=ShowMode.DELETE_AND_SEND)
        elif res.status_code == 420:
            await message.answer(res.json()["error"])
        else:
            logger.warning(f"⚠️ Не удалось отправить код: {res.status_code} {res.text}")
            await message.answer(f"{res.status_code} {res.text}")
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
    phone = dialog_manager.dialog_data.get("phone_number")
    sticker = dialog_manager.dialog_data.get("sticker")

    if not phone or not sticker:
        await message.answer("⚠️ Ошибка: данные утеряны. Попробуйте сначала.")
        return

    try:
        res = requests.post(url=BACKEND_URL + "/catcher/authorize", params={'phone': phone, 'sticker': sticker, 'code': code, 'user_id': dialog_manager.event.from_user.id})
        if res.status_code == 200:
            await dialog_manager.start(MainMenu.MAIN_MENU, show_mode=ShowMode.DELETE_AND_SEND)
        else:
            logger.warning(f"⚠️ Не удалось отправить код: {res.status_code} {res.text}")
            await message.answer(f"Произошла ошибка при отправке кода. Пройдите авторизацию еще раз")
            await dialog_manager.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.DELETE_AND_SEND)
    except Exception as e:
        logger.exception("❌ Ошибка при отправке SMS-кода")
        await dialog_manager.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.DELETE_AND_SEND)
        #await message.answer(f"❌ Ошибка при отправке кода: {str(e)}")

async def on_sms_code_error(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    error: ValueError,
):
    logger.warning("🚫 Ошибка ввода авторизационного кода")
    await message.answer("⚠️ Ошибка кода, попробуйте еще раз")
    await dialog_manager.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.DELETE_AND_SEND)

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
                   on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.EDIT)),
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
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTRY_METHOD, show_mode=ShowMode.EDIT)),
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
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.EDIT)),
        ),
        state=AddClientStates.ENTER_SMS_CODE,
        parse_mode="HTML",
    ),
)
