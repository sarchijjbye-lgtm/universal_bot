from aiogram import Router, types
from bot_init import bot
from utils.sheets import add_order
from config import ADMIN_CHAT_ID
from routers.cart import CART, get_total

order_router = Router()

# Простейшая машина состояний для оформления заказа
USER_STATE = {}   # {user_id: "name" / "phone" / "address"}
ORDER_DATA = {}   # {user_id: {...}}


@order_router.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery):
    uid = callback.from_user.id

    if not CART.get(uid):
        await callback.answer("Корзина пуста.", show_alert=True)
        return

    USER_STATE[uid] = "name"
    ORDER_DATA[uid] = {}

    await callback.message.answer("Введите ваше имя:")
    await callback.answer()


@order_router.message()
async def order_flow(message: types.Message):
    uid = message.from_user.id

    if uid not in USER_STATE:
        # Сообщения, не относящиеся к оформлению заказа, не трогаем
        return

    state = USER_STATE[uid]

    if state == "name":
        ORDER_DATA[uid]["name"] = message.text.strip()
        USER_STATE[uid] = "phone"
        await message.answer("Введите номер телефона:")
        return

    if state == "phone":
        ORDER_DATA[uid]["phone"] = message.text.strip()
        USER_STATE[uid] = "address"
        await message.answer("Введите адрес доставки:")
        return

    if state == "address":
        ORDER_DATA[uid]["address"] = message.text.strip()

        cart = CART.get(uid, [])
        total = get_total(cart)

        items_str = "\n".join(
            f"{i+1}. {x['name']} ({x['variant']}) — {x['price']} ₽"
            for i, x in enumerate(cart)
        )

        order = {
            "tg_id": uid,
            "name": ORDER_DATA[uid]["name"],
            "phone": ORDER_DATA[uid]["phone"],
            "address": ORDER_DATA[uid]["address"],
            "items": items_str,
            "total": total
        }

        # Пишем заказ в Google Sheets
        add_order(order)

        await message.answer("Заказ оформлен! 🚀")

        # Отправляем уведомление администратору
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"Новый заказ:\n\n{items_str}\n\n"
            f"Имя: {order['name']}\nТелефон: {order['phone']}\nАдрес: {order['address']}\n\n"
            f"Итого: {total} ₽"
        )

        # Чистим корзину и состояние
        CART[uid] = []
        USER_STATE.pop(uid, None)
        ORDER_DATA.pop(uid, None)
