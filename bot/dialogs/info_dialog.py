from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Jinja

from bot.utils.statesform import InfoStates, MainMenu

info_dialog = Dialog(
    Window(
        Jinja(
            "ℹ️ <b>О сервисе</b>\n"
            "🔍 <b>Наш сервис 24/7 мониторит коэффициенты приемки на складах Wildberries.</b>\n"
            "📉 <i>Многие склады часто закрыты, и вручную отслеживать слоты неудобно.</i>\n"
            "✅ <b>Мы автоматически ловим наилучшие коэффициенты приемки</b>, чтобы клиенты экономили время и деньги.\n"
            "\n"
            "🚀 <b>Наши преимущества:</b>\n"
            "• ⚡ <b>Самый быстрый парсер на рынке</b>\n"
            "• 🎯 Ловит даже монопаллетные слоты на Электросталь\n"
            "• 🕒 Полная автоматизация без ручного обновления"
        ),
        Row(
            Button(Jinja("⬅️ Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        ),
        state=InfoStates.ABOUT_SERVICE,
        parse_mode="HTML",
    )
)
