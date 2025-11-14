from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from routers.cart import USER_CARTS, get_cart, get_total
from config import ADMIN_CHAT_ID

order_router = Router()


# === FSM ===
class Checkout(StatesGroup):
    choosing_delivery = State()
    entering_address = State()
    entering_name = State()
    entering_phone = State()
    confirm = State()


# === /order ===
@order_router.message(F.text == "📦 Оформить заказ")
async def start_checkout(message: types.Message, state: FSMContext):
    cart = get_cart(message.from_user.id)

    if not cart:
        await message.answer("🛒 Ваша корзина пуста.")
        return

    total = get_total(message.from_user.id)

    await message.answer(
        f"Ваш заказ на сумму <b>{total} ₽</b>.\n\nВыберите способ получения:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery"),
                    InlineKeyboardButton(text="🏬 Самовывоз", callback_data="pickup"),
                ]
            ]
        )
    )

    await state.set_state(Checkout.choosing_delivery)


# === выбор доставки / самовывоза ===
@order_router.callback_query(F.data == "delivery")
async def choose_delivery(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(delivery="delivery")

    await callback.message.answer("Введите адрес доставки:")
    await state.set_state(Checkout.entering_address)
    await callback.answer()


@order_router.callback_query(F.data == "pickup")
async def choose_pickup(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(delivery="pickup")
    await state.update_data(address="Самовывоз")

    await callback.message.answer(
        "Отлично! Самовывоз возможен по адресу:\n"
        "<b>г. Москва, ул. Примерная 10</b>.\n\n"
        "Теперь укажите ваше имя:"
    )

    await state.set_state(Checkout.entering_name)
    await callback.answer()


# === адрес ===
@order_router.message(Checkout.entering_address)
async def take_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)

    await message.answer("Введите ваше имя:")
    await state.set_state(Checkout.entering_name)


# === имя ===
@order_router.message(Checkout.entering_name)
async def take_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    # кнопка поделиться номером
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📱 Поделиться номером", request_contact=True)]
        ]
    )

    await message.answer("Отлично! Теперь отправьте ваш номер:", reply_markup=kb)
    await state.set_state(Checkout.entering_phone)


# === номер телефона ===
@order_router.message(Checkout.entering_phone, F.contact)
async def take_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    await show_confirmation(message, state)


@order_router.message(Checkout.entering_phone)
async def manual_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)

    await show_confirmation(message, state)


# === подтверждение ===
async def show_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = get_cart(message.from_user.id)
    total = get_total(message.from_user.id)

    items_text = "\n".join(
        f"• <b>{item['name']}</b> ({item['variant']}): {item['price']} ₽ x {item['qty']}"
        for item in cart
    )

    text = (
        "🧾 <b>Проверьте ваш заказ:</b>\n\n"
        f"{items_text}\n\n"
        f"📍 Способ получения: {'Доставка' if data['delivery']=='delivery' else 'Самовывоз'}\n"
        f"🏡 Адрес: {data['address']}\n"
        f"🙋 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n\n"
        f"💰 <b>Итого: {total} ₽</b>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"),
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)
    await state.set_state(Checkout.confirm)


# === подтверждение заказа ===
@order_router.callback_query(F.data == "confirm_order")
async def finalize(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()

    cart = get_cart(user_id)
    total = get_total(user_id)

    # отправляем админу
    order_text = (
        f"🆕 <b>Новый заказ</b>\n\n"
        f"👤 {data['name']}\n"
        f"📱 {data['phone']}\n"
        f"📍 {data['address']}\n\n"
        f"<b>Товары:</b>\n" +
        "\n".join(f"— {c['name']} ({c['variant']}) x{c['qty']} = {c['price']} ₽" for c in cart) +
        f"\n\n💰 <b>Итого: {total} ₽</b>"
    )

    await callback.bot.send_message(ADMIN_CHAT_ID, order_text)

    USER_CARTS[user_id] = []  # очищаем корзину
    await state.clear()

    await callback.message.answer(
        "🎉 Спасибо за заказ!\n"
        "Менеджер свяжется с вами в течение <b>24 часов</b>."
    )

    await callback.answer()


@order_router.callback_query(F.data == "cancel_order")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Оформление заказа отменено.")
    await callback.answer()
