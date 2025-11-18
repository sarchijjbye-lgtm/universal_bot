# main.py

import asyncio
from fastapi import FastAPI, Request
from aiogram.types import Update

from bot_init import bot, dp
from config import WEBHOOK_URL, WEBHOOK_PATH

# === IMPORT YOUR ROUTERS ===
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from routers.admin_router import admin_router   # <-- добавлен

# === FastAPI app ===
app = FastAPI()

# === Register routers ===
# Aiogram использует их внутри Dispatcher
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(admin_router)   # <-- добавлен

# === TELEGRAM WEBHOOK ENDPOINT ===
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    update = Update(**(await req.json()))
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "running", "webhook": WEBHOOK_URL}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# === SET WEBHOOK ON STARTUP ===
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"[WEBHOOK] Set to {WEBHOOK_URL}")
