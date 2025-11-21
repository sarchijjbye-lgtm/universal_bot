# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

# ============================
# LOGGING
# ============================
logging.basicConfig(level=logging.INFO)


# ============================
# BOT
# ============================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# ============================
# FSM STORAGE (ВАЖНО!)
# ============================
from aiogram.fsm.storage.memory import MemoryStorage
storage = MemoryStorage()

dp = Dispatcher(storage=storage)


# ============================
# MIDDLEWARES
# ============================

from middlewares.antiflood import AntiFloodMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware
from middlewares.stage import StageMiddleware

# антифлуд
dp.message.middleware(AntiFloodMiddleware())

# обработка ошибок
dp.update.middleware(ErrorHandlerMiddleware())

# стейджи для checkout (НЕ FSM!)
dp.message.middleware(StageMiddleware())
dp.callback_query.middleware(StageMiddleware())


# ============================
# ROUTERS
# ============================
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from routers.admin_router import admin_router
from routers.oil_wizard import oil_router

# порядок подключения важен
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(admin_router)
dp.include_router(oil_router)

print("[INIT] Routers connected. Bot ready.")
