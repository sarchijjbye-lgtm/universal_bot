from aiogram import Router, types
from aiogram.filters import Command
from bot_init import bot

start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🛍 Каталог")],
        [types.KeyboardButton(text="🛒 Корзина")],
    ]
    await message.answer(
        "Привет! Это универсальный магазин-бот.\nВыбери действие:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=kb, resize_keyboard=True
        )
    )
