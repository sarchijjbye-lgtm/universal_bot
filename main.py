import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from fastapi import FastAPI
import uvicorn

from config import BOT_TOKEN
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)

# FastAPI для вебхука (можно удалить если только polling)
app = FastAPI()

@app.on_event("startup")
async def startup():
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="catalog", description="Каталог"),
        BotCommand(command="cart", description="Корзина")
    ])
    print("Bot started.")


# ПУЛЛИНГ локально
if __name__ == "__main__":
    async def run():
        await dp.start_polling(bot)

    asyncio.run(run())
