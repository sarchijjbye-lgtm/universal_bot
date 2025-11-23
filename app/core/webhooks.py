# app/core/webhooks.py

from fastapi import APIRouter, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from app.core.config import config

router = APIRouter()


async def register_routers(dp: Dispatcher):
    """Подключение всех handlers."""
    from app.handlers.start import router as start_router
    from app.handlers.catalog import router as catalog_router
    from app.handlers.product import router as product_router
    from app.handlers.cart import router as cart_router
    from app.handlers.order import router as order_router
    from app.handlers.admin.photo_upload import router as admin_photo_router
    from app.handlers.admin.panel import router as admin_panel_router

    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(product_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(admin_photo_router)
    dp.include_router(admin_panel_router)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update(**data)

    from app.core.bot import bot, dp

    await dp.feed_update(bot, update)
    return {"ok": True}


async def setup_webhook(bot: Bot):
    """
    Устанавливаем webhook при старте.
    """
    if not config.BOT_URL:
        print("[WEBHOOK] BOT_URL отсутствует в .env")
        return

    webhook_url = f"{config.BOT_URL}/webhook"

    print(f"[WEBHOOK] Устанавливаю webhook: {webhook_url}")

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(webhook_url)

    print("[WEBHOOK] Webhook успешно установлен")
