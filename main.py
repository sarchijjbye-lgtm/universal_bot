import asyncio
from fastapi import FastAPI, Request
from aiogram.types import Update

from bot_init import bot, dp
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from config import WEBHOOK_URL

app = FastAPI()


# === Подключаем Aiogram-роутеры к Dispatcher (НЕ к FastAPI!) ===
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)


# === Обработка Telegram webhook ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.process_update(update)
    return "ok"


# === Установка вебхука при старте сервиса ===
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
