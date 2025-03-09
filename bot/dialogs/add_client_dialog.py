from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Jinja
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery

from bot.utils.statesform import AddClientStates, MainMenu
from database.controller.ORM import ORMController

orm_controller = ORMController()

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
    """Подтверждение добавления кабинета и его сохранение в БД"""

    tg_id = callback.from_user.id
    name = manager.find("client_name").get_value() or "Без имени"
    cookies = manager.find("cookies").get_value() or "{}"

    # Проверяем, существует ли уже такой кабинет
    existing_client = await orm_controller.get_client_by_name(tg_id=tg_id, name=name)
    if existing_client:
        await callback.message.answer(f"⚠️ Кабинет <b>{name}</b> уже существует!", parse_mode="HTML")
        await manager.done(show_mode=ShowMode.DELETE_AND_SEND)
        return

    # Добавляем кабинет в базу
    await orm_controller.add_client(tg_id=tg_id, name=name, cookies=cookies)

    # Подтверждающее сообщение пользователю
    await callback.message.answer(f"✅ Кабинет <b>{name}</b> успешно добавлен!", parse_mode="HTML")

    # Закрываем диалог
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


add_client_dialog = Dialog(
    # Шаг 1: Ввод имени кабинета
    Window(
        Jinja(
            "🆕 <b>Добавление кабинета</b>\n\n"
            "📌 <b>Введите название кабинета:</b>\n"
            "✏️ <i>Отправьте сообщение с названием, чтобы продолжить.</i>"
        ),
        TextInput(
            id="client_name",
            on_success=go_to_next_step,
        ),
        Row(
            Button(Jinja("🔙 Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU, show_mode=ShowMode.EDIT)),
        ),
        state=AddClientStates.ENTER_NAME,
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
)
