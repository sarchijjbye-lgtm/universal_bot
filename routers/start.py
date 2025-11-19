# routers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart

from settings import get_setting

start_router = Router()


@start_router.message(CommandStart())
async def start(message: types.Message):

    # ---- Берём кастомный текст из Google Sheets ----
    welcome = get_setting("welcome_message")

    if not welcome:
        welcome = (
            "Привет! 👋\n"
            "Это универсальный магазин-бот.\n"
            "Выберите действие:"
        )

    text = f"{welcome}\n\n👇 Выберите действие:"

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🛍 Каталог")],
            [types.KeyboardButton(text="🛒 Корзина")]
        ],
        resize_keyboard=True
    )

    await message.answer(text, reply_markup=kb)
