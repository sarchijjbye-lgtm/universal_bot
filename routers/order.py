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
from settings import get_setting
from google_sheets import connect_to_sheet

order_router = Router()

# временное хранилище по пользователям
METHOD_STORAGE = {}   # user_id -> "pickup" | "delivery"
ADDRESS_STORAGE = {}  # user_id -> текст адреса


def normalize(text: str | None) -> str:
    if not text:
        return ""
    return (
        text.replace("🏪", "")
            .replace("🚚", "")
            .replace(" ", "")
            .lower()
    )


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

    await callback.message.answer(
        "Выберите способ получения:",
        reply_markup=kb
    )
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

    # ---- Самовывоз ----
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

    # ---- Доставка ----
    if choice == "доставка":
        METHOD_STORAGE[user_id] = "delivery"

        await msg.answer(
            "Введите адрес доставки:",
            reply_markup=ReplyKeyboardRemove()  # убираем клавиатуру с вариантами
        )
        await set_stage("address")
        return


# ============================
#   ADDRESS INPUT (TEXT)
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

    # --- данные из settings ---
    store_name = get_setting("store_name", "Наш магазин")
    finish_text = get_setting("after_order_message", "Спасибо за заказ!")
    pickup_address = get_setting("pickup_address", "")
    orders_sheet_name = get_setting("orders_sheet", "Orders")

    # --- способ получения + адрес ---
    method_raw = METHOD_STORAGE.get(user_id, "delivery")
    if method_raw == "pickup":
        method_human = "Самовывоз"
        address = pickup_address or "Самовывоз"
    else:
        method_human = "Доставка"
        address = ADDRESS_STORAGE.get(user_id, "—")

    phone = msg.contact.phone_number

    # --- красивый список товаров ---
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
        # просто логируем в консоль, чтобы не ломать UX
        print(f"[ORDERS] Ошибка записи в Google Sheets: {e}")

    # ============================
    #   УВЕДОМЛЕНИЕ АДМИНУ
    # ============================

    try:
        admin_from_settings = get_setting("admin_chat_id", "")
        admin_id = admin_from_settings or os.getenv("ADMIN_CHAT_ID", "")
        if admin_id:
            admin_id = int(admin_id)

            admin_text = (
                "📦 <b>Новый заказ</b>\n\n"
                f"👤 Пользователь: <b>{msg.from_user.first_name}</b> "
                f"(id: <code>{user_id}</code>, @{msg.from_user.username})\n"
                f"📞 Телефон: <b>{phone}</b>\n"
                f"🚚 Способ получения: <b>{method_human}</b>\n"
                f"📍 Адрес: <b>{address}</b>\n\n"
                f"🧾 <b>Состав заказа:</b>\n{items_text}\n\n"
                f"💰 <b>Сумма: {total}₽</b>"
            )

            await msg.bot.send_message(admin_id, admin_text)
    except Exception as e:
        print(f"[ORDERS] Ошибка отправки админу: {e}")

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

    # очистка состояния
    clear_cart(user_id)
    METHOD_STORAGE.pop(user_id, None)
    ADDRESS_STORAGE.pop(user_id, None)
    await set_stage(None)
