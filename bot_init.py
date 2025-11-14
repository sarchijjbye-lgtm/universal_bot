# bot_init.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BOT ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# === DISPATCHER ===
dp = Dispatcher()

# === ROUTERS IMPORT ===
# Импортируем все роутеры ПОСЛЕ создания dp,
# чтобы не было ошибок NameError и циклических импортов.

from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router
from routers.debug_photos import debug_photos_router  # <-- теперь здесь ИМПОРТ

# === CONNECT ROUTERS ===
dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(debug_photos_router)  # <-- теперь здесь ПОДКЛЮЧЕНИЕ

print("[INIT] Bot and Dispatcher initialized. Routers connected.")
