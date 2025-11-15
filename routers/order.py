# routers/order.py

from aiogram import Router
from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardMarkup

from routers.cart import get_cart, calc_total
from settings import get_setting

order_router = Router()

# НОРМАЛИЗАТОР ТЕКСТА КНОПОК
def normalize(text: str) -> str:
    """
    Убирает эмодзи и лишние пробелы.
    Чтобы текст кнопок мог быть любым.
    """
    return (
        text.replace("🏬", "")
            .replace("🏪", "")
            .replace("🚚", "")
            .replace("🚛", "")
            .replace("📦", "")
            .replace(" ", "")
            .lower()
    )


# ===== START CHECKOUT =====
@order_router.callback_query(lambda c: c.data == "checkout:start")
async def checkout_start(callback: CallbackQuery, set_stage):

    await set_stage("method")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Самовывоз")],
            [KeyboardButton(text="🚚 Доставка")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await callback.message.answer(
        "Выберите способ получения:",
        reply_markup=kb
    )
    await callback.answer()


# ===== METHOD SELECTED =====
@order_router.message()
async def checkout_method(msg: Message, stage, set_stage):

    if stage != "method":
        return

    user_choice = normalize(msg.text)

    pick = normalize("самовывоз")
    delivery = normalize("доставка")

    # ---- Самовывоз ----
    if pick in user_choice:
        address = get_setting("pickup_address")
        await msg.answer(
            f"🏪 Самовывоз по адресу:\n<b>{address}</b>\n\nТеперь отправьте номер телефона.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
                resize_keyboard=True
            )
        )
        await set_stage("contact")
        return

    # ---- Доставка ----
    if delivery in user_choice:
        await msg.answer(
            "Введите адрес доставки или отправьте геолокацию:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
                resize_keyboard=True
            )
        )
        await set_stage("address")
        return


# ===== ADDRESS =====
@order_router.message(lambda m: m.location is not None or (m.text and m.text.strip()))
async def checkout_address(msg: Message, stage, set_stage):

    if stage != "address":
        return

    await msg.answer(
        "Теперь отправьте номер телефона:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await set_stage("contact")


# ===== CONTACT =====
@order_router.message(lambda m: m.contact is not None)
async def checkout_contact(msg: Message, stage, set_stage):

    if stage != "contact":
        return

    user_id = msg.from_user.id
    cart = get_cart(user_id)
    total = calc_total(user_id)

    shop_name = get_setting("shop_name")
    finish_text = get_setting("post_order_message")

    text = f"""
<b>{shop_name}</b>

Ваш заказ оформлен!  
Сумма: <b>{total}₽</b>

{finish_text}
"""

    await msg.answer(text)
    await set_stage(None)
