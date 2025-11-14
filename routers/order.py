# order.py — PRO CHECKOUT

from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from caching import cache_get
from cart import get_cart, calc_total
from config import ADMIN_CHAT_ID

order_router = Router()


class Checkout(StatesGroup):
    method = State()
    address = State()
    phone = State()
    confirm = State()


@order_router.callback_query(lambda c: c.data == "checkout_start")
async def checkout_start(cb: types.CallbackQuery, state: FSMContext):
    cart = await get_cart(cb.from_user.id)
    if not cart:
        await cb.answer("Корзина пуста")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
            [InlineKeyboardButton("🏪 Самовывоз", callback_data="method_pickup")],
        ]
    )

    await cb.message.answer("Выберите способ получения:", reply_markup=kb)
    await state.set_state(Checkout.method)
    await cb.answer()


@order_router.callback_query(lambda c: c.data.startswith("method_"))
async def choose_method(cb: types.CallbackQuery, state: FSMContext):
    method = cb.data.split("_")[1]
    await state.update_data(method=method)

    if method == "pickup":
        await state.update_data(address="Самовывоз")
        return await request_phone(cb, state)

    await cb.message.answer("Введите адрес доставки:")
    await state.set_state(Checkout.address)
    await cb.answer()


@order_router.message(Checkout.address)
async def set_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await request_phone(message, state)


async def request_phone(event, state):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📱 Поделиться номером", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await event.answer("Отправьте номер телефона:", reply_markup=kb)
    await state.set_state(Checkout.phone)


@order_router.message(Checkout.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = None

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    await state.update_data(phone=phone)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Подтвердить заказ")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Проверьте данные и подтвердите заказ:", reply_markup=kb)
    await state.set_state(Checkout.confirm)


@order_router.message(Checkout.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = await get_cart(message.from_user.id)
    total = calc_total(cart)

    text = (
        f"🆕 <b>Новый заказ</b>\n\n"
        f"Покупатель: @{message.from_user.username}\n"
        f"Метод: {data['method']}\n"
        f"Адрес: {data['address']}\n"
        f"Телефон: {data['phone']}\n\n"
        f"Товаров: {len(cart)}\n"
        f"Итого: <b>{total} ₽</b>\n\n"
        f"Состав:\n"
    )

    for i in cart:
        text += f"• {i['product']} ({i['variant']}) — {i['price']}₽ × {i['qty']}\n"

    await message.answer("Спасибо! В течение 24 часов менеджер свяжется с вами 👌")

    # отправляем админу
    await message.bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")

    # очищаем корзину
    from caching import cache_set
    await cache_set(f"cart:{message.from_user.id}", "[]")

    await state.clear()
