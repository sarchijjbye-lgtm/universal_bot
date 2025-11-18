# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

# ========= BOT =========

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# ========= MIDDLEWARES =========

from middlewares.stage import StageMiddleware
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware

# антифлуд
dp.message.middleware(AntiFloodMiddleware())

# error handler
dp.update.middleware(ErrorHandlerMiddleware())

# стейджи для checkout
dp.message.middleware(StageMiddleware())
dp.callback_query.middleware(StageMiddleware())


# ========= ROUTERS =========

from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from routers.admin_router import admin_router   # <-- добавлен

# Регистрируем все роутеры
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(admin_router)

print("[INIT] Routers connected. Bot ready.")
