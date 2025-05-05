from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Row, Column, Select, Url
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog.widgets.text import Jinja, Const
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timedelta

from bot.utils.statesform import MainMenu, BalanceStates
from database.controller.orm_instance import get_orm
from services.payments.client import TochkaAPIClient
from configurations.payments_config import PaymentsConfig

orm_controller = get_orm()
api = TochkaAPIClient(PaymentsConfig())

# --- Пополнение баланса ---
async def get_balance_data(dialog_manager: DialogManager, **kwargs):
    tg_id = dialog_manager.event.from_user.id
    balance = await orm_controller.balance.get_balance(tg_id)
    tariffs = await orm_controller.get_all_tariffs()
    return {
        "balance": balance,
        "payment_link": dialog_manager.dialog_data.get("payment_link"),
        "amount": dialog_manager.dialog_data.get("amount"),
        "tariffs": tariffs,
    }

amount_options = [("1 000₽", "1000"), ("5 000₽", "5000"), ("25 000₽", "25000")]

async def on_amount_selected(callback: CallbackQuery, widget, manager: DialogManager, amount: str):
    await create_payment_and_proceed(callback.from_user.id, amount, manager)

async def on_custom_amount_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
):
    if not value.isdigit() or int(value) < 1:
        await message.answer("Введите сумму от 1₽", show_alert=True)
        return
    await create_payment_and_proceed(message.from_user.id, value, dialog_manager)

async def create_payment_and_proceed(user_id: int, amount: str, manager: DialogManager):
    config = PaymentsConfig()
    payload = {
        "customerCode": config.get_customer_code(),
        "amount": amount,
        "purpose": f"Пополнение баланса Telegram ID {user_id}",
        "redirectUrl": "https://example.com/success",
        "failRedirectUrl": "https://example.com/fail",
        "consumerId": config.get_consumer_id(),
        "merchantId": config.get_merchant_id(),
        "ttl": 60 * 24 * 7,
        "paymentMode": ["sbp", "card", "tinkoff"]
    }
    payment_link = await api.create_payment_link(payload)
    manager.dialog_data["payment_link"] = payment_link
    manager.dialog_data["amount"] = int(amount)
    await manager.switch_to(BalanceStates.SHOW_PAYMENT)

async def get_payment_link(dialog_manager: DialogManager, **kwargs):
    return {
        "payment_link": dialog_manager.dialog_data.get("payment_link"),
        "amount": dialog_manager.dialog_data.get("amount")
    }

async def on_cancel_payment(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data.clear()
    await callback.answer("❌ Оплата отменена")
    await manager.back()

async def on_subscribe_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    user_id = callback.from_user.id
    balance = await orm_controller.balance.get_balance(user_id)
    if balance < 25000:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return
    await manager.switch_to(BalanceStates.CONFIRM_SUBSCRIPTION)

async def confirm_subscription(callback: CallbackQuery, button: Button, manager: DialogManager):
    user_id = callback.from_user.id
    tariff_id = 1
    now = datetime.utcnow()
    end = now + timedelta(days=30)
    success = await orm_controller.balance.deduct_balance(user_id, 25000)
    if success:
        final_date = await orm_controller.create_subscription(user_id, tariff_id, now, end)
        days_left = (final_date - now).days
        await callback.answer(f"✅ Подписка активна до {final_date.strftime('%d.%m.%Y')} ({days_left} дней)", show_alert=True)
        await manager.done()
    else:
        await callback.answer("❌ Не удалось списать средства", show_alert=True)

# --- Диалог ---
balance_dialog = Dialog(
    Window(
        Jinja("""
        💰 <b>Ваш баланс:</b> <code>{{ balance }}₽</code>

        📦 <b>Тарифы и услуги:</b>
        {% for tariff in tariffs %}
        • {{ tariff.name }}: <b>{{ tariff.price }}₽</b>
        {% endfor %}

        Выберите действие:
        """),
        Column(
            Button(Const("💳 Пополнить баланс"), id="topup",
                   on_click=lambda c, w, m: m.switch_to(BalanceStates.SELECT_AMOUNT)),
            Button(Const("📆 Купить месячную подписку"), id="subscribe", on_click=on_subscribe_click),
            Button(Const("⬅️ Назад"), id="back", on_click=lambda c, w, m: m.start(MainMenu.MAIN_MENU)),
        ),
        state=BalanceStates.MAIN,
        getter=get_balance_data,
        parse_mode="HTML"
    ),
    Window(
        Jinja("""
        💳 <b>Пополнение баланса</b>

        Выберите сумму из списка или введите вручную:
        """),
        TextInput(
            id="custom_amount",
            type_factory=str,
            on_success=on_custom_amount_entered
        ),
        Column(
            Select(
                text=Jinja("{{item[0]}}"),
                id="amount_select",
                item_id_getter=lambda x: x[1],
                items=amount_options,
                on_click=on_amount_selected
            ),
            Button(Const("⬅️ Назад"), id="back_to_balance", on_click=lambda c, w, m: m.back()),
        ),
        state=BalanceStates.SELECT_AMOUNT,
        parse_mode="HTML"
    ),
    Window(
        Jinja("""
<b>Сумма к оплате:</b> <code>{{ amount }}₽</code>
<b>Перейдите по ссылке для оплаты:</b>
"""),
        Column(
            Url(Const("🌐 Перейти к оплате"), url=Jinja("{{ payment_link }}")),
            Button(Const("❌ Отменить оплату"), id="cancel_payment", on_click=on_cancel_payment),
        ),
        state=BalanceStates.SHOW_PAYMENT,
        getter=get_payment_link,
        parse_mode="HTML"
    ),
    Window(
        Const("Вы уверены, что хотите купить месячную подписку за 25 000₽?"),
        Row(
            Button(Const("✅ Подтвердить"), id="confirm_sub", on_click=confirm_subscription),
            Button(Const("❌ Отмена"), id="cancel_sub", on_click=lambda c, w, m: m.back()),
        ),
        state=BalanceStates.CONFIRM_SUBSCRIPTION
    )
)
