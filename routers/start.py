from aiogram import Router, types
from aiogram.filters import Command

start_router = Router()

CATALOG_BUTTON = "🛍 Каталог"    # ← единый текст
CART_BUTTON = "🛒 Корзина"


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text=CATALOG_BUTTON)],
        [types.KeyboardButton(text=CART_BUTTON)],
    ]

    await message.answer(
        "Привет! Это универсальный магазин-бот.\nВыберите действие:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )
    )
