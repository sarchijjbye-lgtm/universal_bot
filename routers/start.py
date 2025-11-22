# routers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from settings import get_setting

start_router = Router()

@start_router.message(CommandStart())
async def start(message: types.Message):
    welcome = get_setting("welcome_message") or (
        "Привет! 👋\n"
        "Это магазин-бот натуральных сыродавленных масел."
    )

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🛍 Каталог")],
            [types.KeyboardButton(text="🧬 Подбор масла")],
            [types.KeyboardButton(text="🛒 Корзина")]
        ],
        resize_keyboard=True
    )

    await message.answer(f"{welcome}\n\n👇 Выберите действие:", reply_markup=kb)
