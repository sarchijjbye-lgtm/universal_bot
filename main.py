# main.py

import asyncio
from fastapi import FastAPI

from aiogram import Bot

from app.core.bot import bot, dp
from app.core.middleware import setup_middlewares
from app.core.webhooks import router as webhook_router, setup_webhook, register_routers
from app.core.config import config

# === Sheets & Catalog services ===
from app.services.sheets.client import GoogleSheetsClient
from app.services.sheets.settings import SettingsService
from app.services.sheets.catalog import CatalogService
from app.services.sheets.orders import OrdersService

# === Other services ===
from app.services.cart import CartService
from app.services.photos import PhotoManager

# === Handlers ===
from app.handlers import start, catalog, product, cart, order
from app.handlers.admin import panel, photo_upload


# ==========================================================
# FastAPI initialization
# ==========================================================
app = FastAPI()
app.include_router(webhook_router)


# ==========================================================
# Application startup
# ==========================================================
@app.on_event("startup")
async def startup_event():

    # 1. Initialize Google Sheets client
    gs_client = GoogleSheetsClient()

    # 2. Load Settings sheet
    settings_service = SettingsService(gs_client)
    settings_service.load()  # updates config

    # 3. Load catalog
    catalog_service = CatalogService(gs_client)
    catalog_service.load()

    # 4. Init other services
    cart_service = CartService(catalog_service)
    orders_service = OrdersService(gs_client)
    photo_manager = PhotoManager(gs_client, catalog_service)

    # 5. Inject services into handlers
    start.catalog_service = catalog_service
    catalog.catalog_service = catalog_service
    product.catalog_service = catalog_service

    cart.catalog_service = catalog_service
    cart.cart_service = cart_service

    order.cart_service = cart_service
    order.orders_service = orders_service

    panel.catalog_service = catalog_service
    photo_upload.photo_manager = photo_manager
    photo_upload.catalog_service = catalog_service

    # 6. Register all routers in DP
    await register_routers(dp)

    # 7. Setup middlewares
    setup_middlewares(dp)

    # 8. Set webhook
    await setup_webhook(bot)

    print("Bot started successfully")


# ==========================================================
# Shutdown
# ==========================================================
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")


# ==========================================================
# Uvicorn Entrypoint for Render
# ==========================================================
# Render запускает командой:
# uvicorn main:app --host 0.0.0.0 --port $PORT
