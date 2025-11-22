# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# === MIDDLEWARES ===
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware
from middlewares.stage import StageMiddleware

dp.message.middleware(AntiFloodMiddleware())
dp.update.middleware(ErrorHandlerMiddleware())

# FSM НЕ трогаем
# кастомный stage — только для order
dp.message.middleware(StageMiddleware())
dp.callback_query.middleware(StageMiddleware())

# === ROUTERS (strict order) ===
# 1. START (реагирует ТОЛЬКО на команду /start)
from routers.start import start_router
dp.include_router(start_router)

# 2. OIL WIZARD (важно чтобы стоял раньше каталога)
from routers.oil_wizard import oil_router
dp.include_router(oil_router)

# 3. основной магазин
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router

dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)

# 4. admin — всегда последний
from routers.admin_router import admin_router
dp.include_router(admin_router)

print("[INIT] All routers connected correctly.")
