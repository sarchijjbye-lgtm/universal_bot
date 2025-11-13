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

# FastAPI для вебхука (можно убрать если polling)
app = FastAPI()

@app.on_event("startup")
async def startup():
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота")
    ])
    print("Bot started.")

@app.post("/webhook")
async def webhook(req):
    await dp.feed_webhook_update(bot, await req.json())
    return {"ok": True}

# ПУЛЛИНГ (локально)
if __name__ == "__main__":
    async def run_polling():
        await dp.start_polling(bot)

    asyncio.run(run_polling())
