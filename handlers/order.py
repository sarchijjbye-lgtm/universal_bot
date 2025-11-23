# app/handlers/order.py

from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.services.cart import CartService
from app.services.sheets.orders import OrdersService
from app.utils.formatting import checkout_preview, admin_order_message
from app.core.config import config

router = Router()

# Эти сервисы будут внедрены из main.py
cart_service: CartService = None
orders_service: OrdersService = None


# ==========================================================
# FSM состояния оформления заказа
# ==========================================================
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_confirm = State()


# ==========================================================
# Шаг 1: Имя
# ==========================================================
@router.message(OrderState.waiting_for_name)
async def order_get_name(message: types.Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Имя слишком короткое. Введите ещё раз.")
        return

    await state.update_data(name=name)
    await message.answer("Введите ваш <b>номер телефона</b>:")

    await state.set_state(OrderState.waiting_for_phone)


# ==========================================================
# Шаг 2: Телефон
# ==========================================================
@router.message(OrderState.waiting_for_phone)
async def order_get_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()

    if len(phone) < 5:
        await message.answer("Похоже, номер телефона слишком короткий. Введите ещё раз.")
        return

    await state.update_data(phone=phone)
    await message.answer("Введите <b>адрес</b> для получения (или напишите: самовывоз):")

    await state.set_state(OrderState.waiting_for_address)


# ==========================================================
# Шаг 3: Адрес
# ==========================================================
@router.message(OrderState.waiting_for_address)
async def order_get_address(message: types.Message, state: FSMContext):
    address = message.text.strip()

    await state.update_data(address=address)

    items = await cart_service.list(state)
    total = await cart_service.total(state)

    await message.answer(
        checkout_preview(items, total)
        + "\n\nПодтвердите заказ:",
        reply_markup=None
    )

    await message.answer(
        "Нажмите кнопку ниже:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✔ Подтвердить заказ",
                        callback_data="order_confirm"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data="order_cancel"
                    )
                ]
            ]
        )
    )

    await state.set_state(OrderState.waiting_for_confirm)


# ==========================================================
# Подтверждение заказа
# ==========================================================
@router.callback_query(lambda c: c.data == "order_confirm")
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")

    items = await cart_service.list(state)
    total = await cart_service.total(state)

    # Создаём заказ
    order_id = orders_service.create_order(
        user_id=callback.from_user.id,
        name=name,
        phone=phone,
        address=address,
        items=items,
        total=total,
    )

    # Отправка админу
    admin_msg = admin_order_message(
        order_id=order_id,
        user_id=callback.from_user.id,
        name=name,
        phone=phone,
        address=address,
        items=items,
        total=total,
    )

    try:
        await callback.bot.send_message(config.ADMIN_CHAT_ID, admin_msg)
    except Exception:
        pass

    # Очистка корзины
    await cart_service.clear(state)

    # Финальное сообщение пользователю
    msg = (
        f"🎉 <b>Спасибо за заказ!</b>\n\n"
        f"Ваш номер заказа: <b>{order_id}</b>\n\n"
        f"{config.AFTER_ORDER_MESSAGE or ''}"
    )

    await callback.message.edit_text(msg)
    await state.clear()


# ==========================================================
# Отмена заказа
# ==========================================================
@router.callback_query(lambda c: c.data == "order_cancel")
async def order_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Заказ отменён.")
    await state.clear()
