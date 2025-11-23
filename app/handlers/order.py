# app/handlers/order.py

from aiogram import Router, types
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.services.cart import CartService
from app.services.sheets.orders import OrdersService
from app.utils.keyboards import confirm_order_kb
from app.utils.formatting import cart_text, total_text, admin_order_message
from app.core.config import config

router = Router()

# Внедряется через main.py
cart_service: CartService = None
orders_service: OrdersService = None


# ==========================================================
# FSM состояния
# ==========================================================
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery_method = State()
    waiting_for_location = State()
    waiting_for_confirm = State()


# ==========================================================
# Старт оформления заказа (нажал "checkout")
# ==========================================================
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    items = await cart_service.list(state)
    total = await cart_service.total(state)

    if not items:
        await callback.answer("Корзина пуста!")
        return

    await callback.message.edit_text(
        cart_text(items) + total_text(total) +
        "\n\nВведите, пожалуйста, ваше <b>имя</b>."
    )
    await state.set_state(OrderState.waiting_for_name)


# ==========================================================
# Шаг 1 — Имя
# ==========================================================
@router.message(OrderState.waiting_for_name)
async def order_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    # Кнопка отправки телефона
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить телефон", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Введите ваш телефон или отправьте его кнопкой ниже:",
        reply_markup=kb
    )
    await state.set_state(OrderState.waiting_for_phone)


# ==========================================================
# Шаг 2 — Телефон
# ==========================================================
@router.message(OrderState.waiting_for_phone)
async def order_phone(message: Message, state: FSMContext):

    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    await state.update_data(phone=phone)

    # Убираем клавиатуру
    await message.answer("Выберите способ получения:", reply_markup=types.ReplyKeyboardRemove())

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🏠 Доставка", callback_data="delivery"),
                types.InlineKeyboardButton(text="🏪 Самовывоз", callback_data="pickup")
            ]
        ]
    )

    await message.answer("Выберите способ получения:", reply_markup=kb)
    await state.set_state(OrderState.waiting_for_delivery_method)


# ==========================================================
# Выбор способа получения
# ==========================================================
@router.callback_query(OrderState.waiting_for_delivery_method)
async def order_delivery_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data
    await state.update_data(method=method)

    if method == "pickup":
        # Самовывоз — адрес из Google Sheets
        await callback.message.edit_text(
            f"🏪 <b>Самовывоз</b>\nАдрес: {config.PICKUP_ADDRESS}\n\n"
            "Проверьте заказ и подтвердите:",
            reply_markup=confirm_order_kb()
        )
        await state.set_state(OrderState.waiting_for_confirm)

    else:
        # Доставка — просим локацию
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await callback.message.answer(
            "Отправьте вашу локацию:", reply_markup=kb
        )
        await state.set_state(OrderState.waiting_for_location)


# ==========================================================
# Получение локации
# ==========================================================
@router.message(OrderState.waiting_for_location)
async def order_location(message: Message, state: FSMContext):
    if not message.location:
        await message.answer("Пожалуйста, отправьте локацию через кнопку ниже.")
        return

    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    await message.answer("Спасибо! Проверьте заказ:", reply_markup=types.ReplyKeyboardRemove())

    items = await cart_service.list(state)
    total = await cart_service.total(state)

    await message.answer(
        cart_text(items) + total_text(total),
        reply_markup=confirm_order_kb()
    )
    await state.set_state(OrderState.waiting_for_confirm)


# ==========================================================
# Подтверждение заказа
# ==========================================================
@router.callback_query(lambda c: c.data == "order_confirm", OrderState.waiting_for_confirm)
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    items = await cart_service.list(state)
    total = await cart_service.total(state)

    # Создаём заказ
    order_id = orders_service.create_order(
        name=data["name"],
        phone=data["phone"],
        delivery_method=data["method"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        items=items,
        total=total
    )

    # Сообщение админу
    await callback.bot.send_message(
        config.ADMIN_CHAT_ID,
        admin_order_message(
            order_id=order_id,
            user_id=callback.from_user.id,
            name=data["name"],
            phone=data["phone"],
            address=data.get("method") == "pickup" and config.PICKUP_ADDRESS or "Доставка",
            items=items,
            total=total
        )
    )

    await callback.message.edit_text("Спасибо! Ваш заказ принят.")
    await cart_service.clear(state)
    await state.clear()


# ==========================================================
# Отмена заказа
# ==========================================================
@router.callback_query(lambda c: c.data == "order_cancel", OrderState.waiting_for_confirm)
async def order_cancel(callback: CallbackQuery, state: FSMContext):
    await cart_service.clear(state)
    await state.clear()

    await callback.message.edit_text("Заказ отменён.")
