from aiogram import Router, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

from routers.cart import get_cart, calc_total, clear_cart
from caching import cache_set
from google_sheets import load_products_safe

order_router = Router()


# ===== STEP 1. START ORDER =====
@order_router.message(lambda m: m.text == "🛒 Оформить заказ")
async def start_order(message: types.Message):
    cart = await get_cart(message.from_user.id)

    if not cart:
        await message.answer("🛒 Ваша корзина пуста!")
        return

    total = calc_total(cart)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚚 Доставка", callback_data="order_delivery"),
            InlineKeyboardButton(text="🏬 Самовывоз", callback_data="order_pickup")
        ]
    ])

    await message.answer(
        f"📦 <b>Оформление заказа</b>\n"
        f"Ваш заказ на сумму <b>{total} ₽</b>\n\n"
        f"Выберите способ получения:",
        reply_markup=kb
    )


# ===== STEP 2A — DELIVERY =====
@order_router.callback_query(lambda c: c.data == "order_delivery")
async def ask_address(callback: types.CallbackQuery):

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await callback.message.answer(
        "Введите адрес доставки или отправьте геолокацию:",
        reply_markup=kb
    )

    await cache_set(f"order:{callback.from_user.id}:stage", "address")
    await callback.answer()


# ===== STEP 2B — PICKUP =====
@order_router.callback_query(lambda c: c.data == "order_pickup")
async def pickup_selected(callback: types.CallbackQuery):

    await cache_set(f"order:{callback.from_user.id}:method", "pickup")

    await callback.message.answer(
        "<b>🏬 Самовывоз выбран</b>\n"
        "Адрес: Москва, ул. Приречная 7\n\n"
        "Теперь отправьте ваш номер телефона👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    await cache_set(f"order:{callback.from_user.id}:stage", "phone")
    await callback.answer()


# ===== STEP 3 — ADDRESS HANDLING =====
@order_router.message(lambda m: True, flags={"stage": "address"})
async def save_address(message: types.Message):
    uid = message.from_user.id

    if message.location:
        address = f"Геолокация: {message.location.latitude}, {message.location.longitude}"
    else:
        address = message.text

    await cache_set(f"order:{uid}:address", address)
    await cache_set(f"order:{uid}:method", "delivery")
    await cache_set(f"order:{uid}:stage", "phone")

    await message.answer(
        "Теперь отправьте ваш номер телефона👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


# ===== STEP 4 — PHONE =====
@order_router.message(lambda m: m.contact or m.text.startswith("+"))
async def receive_phone(message: types.Message):
    uid = message.from_user.id

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    await cache_set(f"order:{uid}:phone", phone)

    cart = await get_cart(uid)
    products = await load_products_safe()
    total = calc_total(cart)

    method = await cache_set(f"order:{uid}:method")
    address = await cache_set(f"order:{uid}:address")

    # FINISH
    await clear_cart(uid)

    await message.answer(
        "🎉 <b>Ваш заказ принят!</b>\n\n"
        "Менеджер свяжется с вами в течение 24 часов 🙌\n\n"
        f"📱 Ваш номер: <b>{phone}</b>",
        reply_markup=types.ReplyKeyboardRemove()
    )
