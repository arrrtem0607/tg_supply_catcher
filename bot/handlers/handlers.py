from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import DialogManager, ShowMode
from database import get_orm
from bot.utils.statesform import MainMenu


orm_controller = get_orm()
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    response = await orm_controller.register_user(user_id, username)

    if response.get("message") == "Пользователь уже зарегистрирован":
        msg_text = "Привет! Ты уже зарегистрирован в системе 🚀"
        show_menu = True  # Показываем меню
    elif "error" in response:
        msg_text = f"❌ Ошибка регистрации: {response['error']}"
        show_menu = False  # Не показываем меню
    else:
        msg_text = "Привет! Ты зарегистрирован в системе 🎉"
        show_menu = True  # Показываем меню

    # Отправляем сообщение пользователю
    await message.answer(msg_text)

    # Если не было ошибки, запускаем стартовое меню
    if show_menu:
        await dialog_manager.start(state=MainMenu.MAIN_MENU, show_mode=ShowMode.DELETE_AND_SEND)

