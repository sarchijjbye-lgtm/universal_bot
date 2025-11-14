from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

# === LOGGING ===
import logging
logging.basicConfig(level=logging.INFO)


# === BOT ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# === DISPATCHER ===
dp = Dispatcher()


# === IMPORT & CONNECT ROUTERS ===
# (импортируем здесь, чтобы не было циклических импортов)
from routers.start import start_router
from routers.catalog import catalog_router
from routers.cart import cart_router
from routers.order import order_router


dp.include_router(start_router)
dp.include_router(catalog_router)
dp.include_router(cart_router)
dp.include_router(order_router)

print("[INIT] Bot and Dispatcher initialized. Routers connected.")
