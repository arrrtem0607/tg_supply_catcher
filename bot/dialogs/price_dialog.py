from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Jinja

from bot.utils.statesform import MainMenu, PriceStates

price_dialog = Dialog(
    Window(
        Jinja(
            "💸 <b>Тарифы и цены</b>\n"
            "🔹 <b>Подписки:</b>\n"
            "• 📆 Месячная подписка: <b>25 000₽</b>\n"
            "• 🏆 Бессрочная подписка: <b>100 000₽</b>\n"
            "\n"
            "🔹 <b>Разовые отловы:</b>\n"
            "• 📦 Одна коробная поставка: <b>1 000₽</b>\n"
            "• 🏗️ Одна монопаллетная поставка: <b>1 500₽</b>\n"
            "\n"
            "🎁 <b>Бонус:</b> 3 бесплатных отлова при регистрации!"
        ),
        Row(
            Button(Jinja("⬅️ Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        ),
        state=PriceStates.PRICE_INFO,
        parse_mode="HTML",
    )
)
