import logging
from fastapi import FastAPI, Request
from aiogram.types import Update

from bot_init import bot, dp
from config import WEBHOOK_URL

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# === Роутеры Aiogram ===
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router

dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)


# === WEBHOOK HANDLER ===
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    logging.info(f"[WEBHOOK] Update received: {body}")

    update = Update(**body)
    await dp.feed_update(bot, update)
    return "ok"


# === STARTUP ===
@app.on_event("startup")
async def on_startup():
    logging.info(f"[WEBHOOK] Setting webhook: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
