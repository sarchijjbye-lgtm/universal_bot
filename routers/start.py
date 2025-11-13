from aiogram import Router, types
from aiogram.filters import Command

start_router = Router()

@start_router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "📦 Каталог: /catalog\n"
        "🛒 Корзина: /cart"
    )
