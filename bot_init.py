# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

print("[INIT] Logging initialized")


# =========================
# BOT
# =========================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

print("[INIT] Bot instance created")


# =========================
# DISPATCHER
# =========================
dp = Dispatcher()

print("[INIT] Dispatcher created")


# =====================================================
#   MIDDLEWARES (очень важно!)
# =====================================================

# --- Stage middleware для order.py ---
from middlewares.stage import StageMiddleware
dp.message.middleware(StageMiddleware())

# --- Error handler (бот не падает в проде) ---
from middlewares.error_handler import ErrorHandlerMiddleware
dp.update.middleware(ErrorHandlerMiddleware())

# --- Antiflood (защита от спама) ---
from middlewares.antiflood import AntiFloodMiddleware
dp.message.middleware(AntiFloodMiddleware(limit=0.5))


print("[INIT] Middlewares registered")


# =====================================================
#   ROUTERS
# =====================================================

# Импортируем все роутеры ТОЛЬКО ПОСЛЕ создания dp и middleware

from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from routers.debug_photos import debug_photos_router

# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(debug_photos_router)

print("[INIT] Routers connected: start, catalog, cart, order, debug_photos")
print("[INIT] Bot init complete!")
