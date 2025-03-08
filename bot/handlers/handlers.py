from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import DialogManager, ShowMode
from database.controller.ORM import ORMController
from bot.utils.statesform import MainMenu

orm_controller = ORMController()
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # ✅ Добавляем пользователя в базу
    await orm_controller.add_user(user_id, username)

    await dialog_manager.event.bot.send_message(text="Привет! Ты зарегистрирован в системе 🎉", chat_id=user_id)
    await dialog_manager.start(state=MainMenu.MAIN_MENU, show_mode=ShowMode.DELETE_AND_SEND)
