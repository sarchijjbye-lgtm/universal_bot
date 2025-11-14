# routers/order.py

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from routers.cart import CART, get_total
from utils.sheets import add_order
from config import ADMIN_CHAT_ID

import datetime

order_router = Router()


# ========== FSM ==========
class OrderFSM(StatesGroup):
    choosing_method = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    confirm = State()


# ========== START CHECKOUT ==========
@order_router.message(F.text == "📦 Оформить заказ")
async def start_checkout(message: types.Message, state: FSMContext):
    cart = CART.get(message.from_user.id, {})

    if not cart:
        await message.answer("🛒 Ваша корзина пуста.")
        return

    # выбор способа получения
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Доставка", callback_data="method_delivery")],
        [InlineKeyboardButton(text="🏬 Самовывоз", callback_data="method_pickup")]
    ])

    await state.set_state(OrderFSM.choosing_method)
    await message.answer("Как хотите получить заказ?", reply_markup=kb)


# ========== SPOSOB POLUCHENIYA ==========
@order_router.callback_query(F.data.startswith("method_"))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.replace("method_", "")
    await state.update_data(method=method)

    await callback.message.answer("Введите ваше имя:")
    await state.set_state(OrderFSM.waiting_name)
    await callback.answer()


# ========== NAME ==========
@order_router.message(OrderFSM.waiting_name)
async def set_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    # спрашиваем телефон кнопкой
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(OrderFSM.waiting_phone)
    await message.answer("Отправьте номер телефона:", reply_markup=kb)


# ========== PHONE (BUTTON) ==========
@order_router.message(OrderFSM.waiting_phone, F.contact)
async def phone_shared(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    await ask_address_or_confirm(message, state)


# ========== PHONE (TYPED) ==========
@order_router.message(OrderFSM.waiting_phone)
async def phone_typed(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)

    await ask_address_or_confirm(message, state)


# ========== ASK ADDRESS IF DELIVERY ==========
async def ask_address_or_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if data["method"] == "delivery":
        await state.set_state(OrderFSM.waiting_address)
        await message.answer(
            "Укажите адрес доставки:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        # самовывоз → сразу к подтверждению
        await state.update_data(address="-")
        await show_confirmation(message, state)


# ========== ADDRESS ==========
@order_router.message(OrderFSM.waiting_address)
async def set_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await show_confirmation(message, state)


# ========== SHOW CONFIRM PAGE ==========
async def show_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id

    cart = CART.get(user_id, {})
    total = get_total(user_id)

    products_text = "\n".join(
        [f"• {item} × {info['quantity']} = {info['price'] * info['quantity']} ₽"
         for item, info in cart.items()]
    )

    text = f"""
<b>🧾 Проверьте заказ</b>

<b>Имя:</b> {data['name']}
<b>Телефон:</b> {data['phone']}
<b>Тип получения:</b> {"Доставка" if data['method']=="delivery" else "Самовывоз"}
<b>Адрес:</b> {data['address']}

<b>🛒 Товары:</b>
{products_text}

<b>Итого:</b> {total} ₽
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="order_confirm")],
        [InlineKeyboardButton(text="🔄 Изменить", callback_data="order_edit")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="order_cancel")]
    ])

    await state.set_state(OrderFSM.confirm)
    await message.answer(text, reply_markup=kb)


# ========== EDIT ==========
@order_router.callback_query(F.data == "order_edit")
async def order_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Начнем заново. Введите ваше имя:")
    await state.set_state(OrderFSM.waiting_name)
    await callback.answer()


# ========== CANCEL ==========
@order_router.callback_query(F.data == "order_cancel")
async def order_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Оформление заказа отменено.", reply_markup=types.ReplyKeyboardRemove())
    await callback.answer()


# ========== CONFIRM ==========
@order_router.callback_query(F.data == "order_confirm")
async def order_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    cart = CART.get(user_id, {})
    total = get_total(user_id)

    # запись в Google Sheets
    add_order({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": data["name"],
        "phone": data["phone"],
        "method": data["method"],
        "address": data["address"],
        "total": total,
        "items": str(cart)
    })

    # уведомление админу
    products_text = "\n".join(
        [f"• {item} × {info['quantity']} = {info['price'] * info['quantity']} ₽"
         for item, info in cart.items()]
    )

    admin_text = f"""
🔔 <b>НОВЫЙ ЗАКАЗ</b>

<b>Имя:</b> {data['name']}
<b>Телефон:</b> {data['phone']}
<b>Тип:</b> {"Доставка" if data['method']=="delivery" else "Самовывоз"}
<b>Адрес:</b> {data['address']}
<b>Сумма:</b> {total} ₽

<b>🛒 Товары:</b>
{products_text}
"""

    await callback.bot.send_message(ADMIN_CHAT_ID, admin_text)

    # сообщение пользователю
    await callback.message.answer(
        "🎉 <b>Спасибо!</b>\nВаш заказ принят.\nМенеджер свяжется с вами в течение 24 часов.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # очищаем корзину
    CART[user_id] = {}

    await state.clear()
    await callback.answer()
