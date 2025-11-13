from aiogram import Router, types

start_router = Router()

@start_router.message(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "📦 Каталог: /catalog\n"
        "🛒 Корзина: /cart"
    )
