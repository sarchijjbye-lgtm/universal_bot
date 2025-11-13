import asyncio
from fastapi import FastAPI
from aiogram import Bot
from aiogram.types import Update
from fastapi import Request

from bot_init import bot, dp
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from config import WEBHOOK_URL

app = FastAPI()


# === Подключение роутеров ===
app.include_router(start_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(order_router)


# === Обработка Telegram webhook ===
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update(**data)
    await dp.process_update(update)
    return "ok"


# === Установка вебхука ===
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
