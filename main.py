import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Request
import uvicorn

from config import BOT_TOKEN
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)

# URL вебхука (Render задаёт domain)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://universal-bot-eb3x.onrender.com/webhook" # обновим после деплоя

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)

    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="catalog", description="Каталог"),
        BotCommand(command="cart", description="Корзина"),
    ])
    print("Webhook set!")


@app.post(WEBHOOK_PATH)
async def process_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
