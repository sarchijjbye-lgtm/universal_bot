# routers/order.py

from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from datetime import datetime
import os

from routers.cart import get_cart, calc_total, clear_cart
from google_sheets import connect_to_sheet, update_stock, load_products_safe
from settings import get_setting

order_router = Router()

METHOD_STORAGE = {}
ADDRESS_STORAGE = {}

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))


def normalize(text: str | None):
    if not text:
        return ""
    return text.replace("🏪", "").replace("🚚", "").replace(" ", "").lower()


# ============================
#   START CHECKOUT
# ============================

@order_router.callback_query(lambda c: c.data == "checkout:start")
async def checkout_start(callback: CallbackQuery, set_stage):

    await set_stage("method")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Самовывоз")],
            [KeyboardButton(text="🚚 Доставка")],
        ],
        resize_keyboard=True
    )

    await callback.message.answer("Выберите способ получения:", reply_markup=kb)
    await callback.answer()


# ============================
#   METHOD SELECTOR
# ============================

@order_router.message(lambda m: normalize(m.text) in ["самовывоз", "доставка"])
async def checkout_method(msg: Message, stage, set_stage):

    if stage != "method":
        return

    user_id = msg.from_user.id
    choice = normalize(msg.text)

    if choice == "самовывоз":
        METHOD_STORAGE[user_id] = "pickup"
        address = get_setting("pickup_address")

        await msg.answer(
            f"🏪 Самовывоз по адресу:\n<b>{address}</b>\n\nТеперь отправьте номер телефона:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
                resize_keyboard=True
            )
        )
        await set_stage("contact")
        return

    if choice == "доставка":
        METHOD_STORAGE[user_id] = "delivery"

        await msg.answer(
            "Введите адрес доставки:",
            reply_markup=ReplyKeyboardRemove()
        )
        await set_stage("address")
        return


# ============================
#   ADDRESS INPUT
# ============================

@order_router.message(lambda m: m.text and len(m.text) > 3)
async def checkout_address_text(msg: Message, stage, set_stage):

    if stage != "address":
        return

    user_id = msg.from_user.id
    ADDRESS_STORAGE[user_id] = msg.text.strip()

    await msg.answer(
        "Спасибо! Теперь отправьте номер телефона:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await set_stage("contact")


# ============================
#   CONTACT (PHONE)
# ============================

@order_router.message(lambda m: m.contact is not None)
async def checkout_contact(msg: Message, stage, set_stage):

    if stage != "contact":
        return

    user_id = msg.from_user.id
    cart = get_cart(user_id)
    total = calc_total(user_id)

    store_name = get_setting("store_name", "Наш магазин")
    finish_text = get_setting("after_order_message", "Спасибо за заказ!")
    pickup_address = get_setting("pickup_address", "")
    orders_sheet_name = get_setting("orders_sheet", "Orders")

    method_raw = METHOD_STORAGE.get(user_id, "delivery")

    if method_raw == "pickup":
        method_human = "Самовывоз"
        address = pickup_address or "Самовывоз"
    else:
        method_human = "Доставка"
        address = ADDRESS_STORAGE.get(user_id, "—")

    phone = msg.contact.phone_number

    if cart:
        items_lines = [
            f"• {item['name']} ({item['variant']}) — {item['price']}₽ × {item['qty']} = {item['price'] * item['qty']}₽"
            for item in cart
        ]
        items_text = "\n".join(items_lines)
    else:
        items_text = "— корзина пуста (ошибка?)"

    # ============================
    #   ЗАПИСЬ В GOOGLE SHEETS
    # ============================

    try:
        ws = connect_to_sheet(orders_sheet_name)
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(user_id),
            msg.from_user.username or "",
            f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip(),
            method_human,
            address,
            phone,
            items_text,
            total
        ])
    except Exception as e:
        print(f"[ORDERS] Ошибка записи в Google Sheets: {e}")

    # ============================
    #   СПИСАНИЕ STOCK
    # ============================

    products = load_products_safe()

    for item in cart:
        child_id = item["child_id"]
        qty = item["qty"]

        product = next((x for x in products if x["id"] == child_id), None)
        if not product:
            continue

        old_stock = product["stock"]

        if old_stock is None:
            continue  # товар без контроля стока

        new_stock = old_stock - qty
        if new_stock < 0:
            new_stock = 0

        updated = update_stock(child_id, new_stock)

        # ============================
        #   УВЕДОМЛЕНИЕ АДМИНУ
        # ============================

        if ADMIN_CHAT_ID:

            # закончилось
            if new_stock == 0:
                await msg.bot.send_message(
                    ADMIN_CHAT_ID,
                    f"❗ Товар <b>{product['name']} {product['variant_label']}</b> закончился (stock = 0).\n"
                    f"active → FALSE"
                )

            # мало товара
            elif new_stock <= 3:
                await msg.bot.send_message(
                    ADMIN_CHAT_ID,
                    f"⚠️ Товар <b>{product['name']} {product['variant_label']}</b> заканчивается.\n"
                    f"Осталось: {new_stock} шт."
                )

    # ============================
    #   СООБЩЕНИЕ ПОКУПАТЕЛЮ
    # ============================

    user_text = (
        f"<b>{store_name}</b>\n\n"
        f"Ваш заказ оформлен! 🙌\n\n"
        f"🚚 Способ получения: <b>{method_human}</b>\n"
        f"📍 Адрес: <b>{address}</b>\n"
        f"📞 Телефон: <b>{phone}</b>\n\n"
        f"🧾 <b>Состав заказа:</b>\n{items_text}\n\n"
        f"💰 <b>Итого: {total}₽</b>\n\n"
        f"{finish_text}"
    )

    await msg.answer(user_text, reply_markup=ReplyKeyboardRemove())

    clear_cart(user_id)
    METHOD_STORAGE.pop(user_id, None)
    ADDRESS_STORAGE.pop(user_id, None)
    await set_stage(None)
