# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

# ============================
# BOT
# ============================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# ============================
# MIDDLEWARES
# ============================

from middlewares.antiflood import AntiFloodMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware
from middlewares.stage import StageMiddleware

dp.message.middleware(AntiFloodMiddleware())
dp.update.middleware(ErrorHandlerMiddleware())
dp.message.middleware(StageMiddleware())
dp.callback_query.middleware(StageMiddleware())

# ============================
# ROUTERS (ПРАВИЛЬНЫЙ ПОРЯДОК)
# ============================

# 1. Сначала — подбор масла (ловит текст кнопки)
from routers.oil_wizard import oil_router
dp.include_router(oil_router)

# 2. Потом — старт, каталог, корзина
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router

dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)

# 3. Админ — в конце
from routers.admin_router import admin_router
dp.include_router(admin_router)

print("[INIT] Routers connected in correct order. Bot ready.")
