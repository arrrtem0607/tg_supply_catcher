import json
import logging

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Row, Column
from aiogram_dialog.widgets.text import Jinja, Const
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery

from bot.utils.statesform import AddClientStates, MainMenu
from database.controller.ORM import ORMController
from bot.utils.wildberries_api import WildberriesAPI

orm_controller = ORMController()
wb_api = WildberriesAPI()
logger = logging.getLogger(__name__)

async def on_choose_cookies(c, w, m):
    await m.switch_to(AddClientStates.ENTER_NAME, show_mode=ShowMode.EDIT)

async def on_choose_phone(c, w, m):
    await m.switch_to(AddClientStates.ENTER_PHONE, show_mode=ShowMode.EDIT)

async def get_client_data(dialog_manager: DialogManager, **kwargs):
    """Передача имени кабинета и Cookies в шаблон"""
    return {
        "client_name": dialog_manager.find("client_name").get_value() or "Без имени",
        "cookies": dialog_manager.find("cookies").get_value() or "Нет данных"
    }

async def go_to_next_step(message: Message, widget, manager: DialogManager, value: str):
    """Функция для перехода к следующему шагу"""
    await manager.next(show_mode=ShowMode.DELETE_AND_SEND)

async def confirm_client_data(callback: CallbackQuery, widget, manager: DialogManager):
    """Подтверждение добавления кабинета, регистрация через API и сохранение в БД."""

    tg_id = callback.from_user.id
    name = manager.find("client_name").get_value() or "Без имени"
    cookies = manager.find("cookies").get_value() or "{}"

    # ✅ Вызываем ORM-контроллер для регистрации клиента
    result = await orm_controller.register_client(tg_id, name, cookies)

    if "error" in result:
        await callback.message.answer(f"❌ {result['error']}", parse_mode="HTML")
    else:
        client_id = result["client_id"]
        await callback.message.answer(
            f"✅ Кабинет <b>{name}</b> успешно добавлен! 🎉\n"
            f"🔑 <b>ID клиента:</b> {client_id}",
            parse_mode="HTML"
        )

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)

async def on_sms_code_entered(message: Message, widget, manager: DialogManager, value: str):
    """Обработка ввода SMS-кода, авторизация в Wildberries и регистрация клиента"""
    sms_code = value.strip()
    phone = manager.dialog_data.get("phone_number")

    # ⛔ Проверяем, что объект API был сохранён
    api: WildberriesAPI = manager.dialog_data.get("api")
    if not api:
        await message.answer("⚠️ Ошибка: сессия авторизации не найдена.")
        await manager.done(show_mode=ShowMode.DELETE_AND_SEND)
        return

    try:
        # 🔐 Пытаемся авторизоваться
        api.authorize(sms_code)

        # 💾 Получаем cookies из сессии
        cookies_dict = api.session.cookies.get_dict()
        cookies_json = json.dumps(cookies_dict)

        # 📛 Генерируем имя по номеру
        name = f"Клиент {phone[-4:]}" if phone else "Новый клиент"
        tg_id = message.from_user.id

        # ✅ Регистрируем клиента через ORM
        result = await orm_controller.register_client(tg_id, name, cookies_json)

        if "error" in result:
            await message.answer(f"❌ {result['error']}")
        else:
            await message.answer(
                f"✅ Клиент по номеру <b>{phone}</b> успешно добавлен!\n"
                f"🔑 ID: <code>{result['client_id']}</code>",
                parse_mode="HTML"
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка авторизации: {str(e)}")

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)

async def get_phone_number(d, **kwargs):
    return {"phone_number": d.dialog_data.get("phone_number", "неизвестен")}

#____________________________
async def on_phone_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    phone: str,
):
    logger.info(f"📞 Введён номер телефона: {phone}")
    dialog_manager.dialog_data["phone_number"] = phone

    # Создаем экземпляр API и сохраняем в dialog_data
    api = WildberriesAPI(phone_number=phone)
    dialog_manager.dialog_data["api"] = api

    logger.info("📡 Отправка запроса на получение SMS-кода...")

    try:
        success = api.send_code()
        if success:
            logger.info("✅ SMS-код успешно отправлен.")
            await dialog_manager.switch_to(AddClientStates.ENTER_SMS_CODE)
        else:
            logger.warning("⚠️ Не удалось отправить код. Ответ не OK.")
            await message.answer("❌ Не удалось отправить код. Попробуйте позже.")
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
    # Шаг 2: Инструкция + Ввод Cookies
    Window(
        Jinja(
            "🆕 <b>Добавление кабинета</b>\n\n"
            "📌 Кабинет: <b>{{ client_name }}</b>\n\n"
            "📜 <b>Как получить Cookies?</b>\n\n"
            "1️⃣ Установите расширение <b>Cookie-Editor</b> для вашего браузера.\n"
            "2️⃣ Авторизуйтесь в кабинете WB.\n"
            "3️⃣ Откройте <b>Cookie-Editor</b>, найдите <code>WBToken</code> и <code>WBAuth</code>.\n"
            "4️⃣ Скопируйте их и отправьте сюда в формате:\n"
            "<code>{\"WBToken\": \"ваш_токен\", \"WBAuth\": \"ваш_токен\"}</code>\n\n"
            "✏️ <i>Введите Cookies в ответном сообщении, чтобы продолжить.</i>"
        ),
        TextInput(
            id="cookies",
            on_success=go_to_next_step,
        ),
        Row(
            Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_NAME, show_mode=ShowMode.EDIT)),
        ),
        state=AddClientStates.ENTER_COOKIES,
        getter=get_client_data,
        parse_mode="HTML",
    ),

    # Шаг 3: Подтверждение данных
    Window(
        Jinja(
            "✅ <b>Подтверждение данных</b>\n\n"
            "📌 <b>Кабинет:</b> {{ client_name }}\n"
            "🔑 <b>Cookies:</b> <code>{{ cookies }}</code>\n\n"
            "Все верно?"
        ),
        Row(
            Button(Jinja("✅ Подтвердить"), id="confirm", on_click=confirm_client_data),
            Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_COOKIES, show_mode=ShowMode.EDIT)),
        ),
        state=AddClientStates.CONFIRMATION,
        getter=get_client_data,
        parse_mode="HTML",
    ),
    Window(
        Jinja(
            "📱 <b>Добавление по номеру телефона</b>\n\n"
            "📞 <b>Введите номер телефона в формате:</b>\n"
            "<code>+79991234567</code>\n"
            "✏️ <i>После ввода мы отправим код подтверждения.</i>"
        ),
        TextInput(
            id="phone_number",
            on_success=on_phone_entered,
        ),
        Row(
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTRY_METHOD)),
        ),
        state=AddClientStates.ENTER_PHONE,
        parse_mode="HTML",
    ),
    Window(
        Jinja(
            "📲 <b>Введите код из SMS</b>\n\n"
            "💬 Мы отправили код на номер <b>{{ phone_number }}</b>\n"
            "✏️ <i>Введите код для завершения авторизации</i>"
        ),
        TextInput(
            id="sms_code",
            on_success=on_sms_code_entered,
        ),
        Row(
            Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.switch_to(AddClientStates.ENTER_PHONE)),
        ),
        state=AddClientStates.ENTER_SMS_CODE,
        parse_mode="HTML",
        getter=get_phone_number,
    )
)
