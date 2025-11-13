from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_CHAT_ID
from utils.sheets import add_order
from routers.cart import user_carts
from main import bot

order_router = Router()

class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()

@order_router.callback_query(F.data == "make_order")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите имя:")
    await state.set_state(OrderForm.name)

@order_router.message(OrderForm.name)
async def ask_phone(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите телефон:")
    await state.set_state(OrderForm.phone)

@order_router.message(OrderForm.phone)
async def ask_address(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите адрес доставки:")
    await state.set_state(OrderForm.address)

@order_router.message(OrderForm.address)
async def finish_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = message.from_user.id
    cart = user_carts.get(uid, [])

    items_str = "; ".join([
        f"{i['name']}" + (f" ({i['variant_label']})" if i['variant_label'] else "")
        + f" x{i['qty']} [{i['price']}]"
        for i in cart
    ])

    total = sum(i["price"] * i["qty"] for i in cart)

    order = {
        "tg_id": str(uid),
        "name": data["name"],
        "phone": data["phone"],
        "address": message.text,
        "items": items_str,
        "total": total
    }

    add_order(order)
    user_carts[uid] = []

    await message.answer("✅ Заказ оформлен! С вами свяжется оператор.")

    await bot.send_message(
        ADMIN_CHAT_ID,
        f"📦 Новый заказ\n\n"
        f"Имя: {order['name']}\n"
        f"Телефон: {order['phone']}\n"
        f"Адрес: {order['address']}\n\n"
        f"Товары: {order['items']}\n"
        f"Сумма: {order['total']} ₽"
    )

    await state.clear()
