# main.py

import asyncio
from fastapi import FastAPI

from app.core.bot import bot, dp
from app.core.config import config
from app.core.middleware import setup_middlewares
from app.core.webhooks import router as webhook_router
from app.core.webhooks import setup_webhook, register_routers

# === Google Sheets Services ===
from app.services.sheets.client import GoogleSheetsClient
from app.services.sheets.settings import SettingsService
from app.services.sheets.catalog import CatalogService
from app.services.sheets.orders import OrdersService

# === Internal App Services ===
from app.services.cart import CartService
from app.services.photos import PhotoManager

# === Handlers (DI injection) ===
from app.handlers import start, catalog, product, cart, order
from app.handlers.admin import panel, photo_upload


# ==========================================================
# FastAPI Init
# ==========================================================
app = FastAPI()
app.include_router(webhook_router)


# ==========================================================
# STARTUP
# ==========================================================
@app.on_event("startup")
async def startup_event():
    print("▶ STARTUP: Initializing services...")

    # 1 — Google Sheets Client
    gs = GoogleSheetsClient()

    # 2 — Load Settings
    settings_service = SettingsService(gs)
    settings_service.load()        # config.update_sheet_settings(...)

    # 3 — Load Catalog
    catalog_service = CatalogService(gs)
    catalog_service.load()

    # 4 — Other services
    cart_service = CartService(catalog_service)
    orders_service = OrdersService(gs)
    photo_manager = PhotoManager(gs, catalog_service)

    # 5 — Inject services into handlers
    start.catalog_service = catalog_service
    catalog.catalog_service = catalog_service
    product.catalog_service = catalog_service

    cart.catalog_service = catalog_service
    cart.cart_service = cart_service

    order.catalog_service = catalog_service
    order.cart_service = cart_service
    order.orders_service = orders_service

    panel.catalog_service = catalog_service
    photo_upload.catalog_service = catalog_service
    photo_upload.photo_manager = photo_manager

    # 6 — Register all routers
    await register_routers(dp)

    # 7 — Middlewares
    setup_middlewares(dp)

    # 8 — Webhook
    await setup_webhook(bot)

    print("✅ Bot started successfully")


# ==========================================================
# SHUTDOWN
# ==========================================================
@app.on_event("shutdown")
async def shutdown_event():
    print("⛔ Bot shutdown")


# ==========================================================
# Render Entrypoint
# ==========================================================
# uvicorn main:app --host 0.0.0.0 --port $PORT

