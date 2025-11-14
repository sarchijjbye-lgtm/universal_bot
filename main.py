# main.py — PRODUCTION EDITION v2

import time
import asyncio
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest
from starlette.middleware.base import BaseHTTPMiddleware

from bot_init import bot, dp
from config import (
    WEBHOOK_URL, WEBHOOK_PATH,
    ADMIN_CHAT_ID,
    REDIS_URL
)
from utils.files import preload_all_images
from caching import redis_client
from google_sheets import connect_to_sheet

# ====== CONSTANTS ======
MAX_UPDATE_DELAY = 25
MAX_REQUEST_SIZE = 5 * 1024 * 1024
RATE_LIMIT_MSG = 0.4
RATE_LIMIT_CB = 0.25

metrics = {
    "updates_total": 0,
    "messages": 0,
    "callbacks": 0,
    "errors": 0,
    "start_time": time.time(),
}

last_msg = {}
last_cb = {}

app = FastAPI()


# ============ MIDDLEWARES ============

class RequestSizeLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        body = await request.body()
        if len(body) > MAX_REQUEST_SIZE:
            raise HTTPException(413, "Payload too large")
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"[HTTP] {request.method} {request.url}")
        return await call_next(request)


app.add_middleware(RequestSizeLimiterMiddleware)
app.add_middleware(LoggingMiddleware)


# ============ SEND ERROR TO ADMIN ============

async def notify_admin(text: str):
    try:
        await bot.send_message(ADMIN_CHAT_ID, f"⚠️ ERROR:\n{text}")
    except:
        pass


# ============ TELEGRAM WEBHOOK ============

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        raw = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    update = Update(**raw)
    metrics["updates_total"] += 1

    uid = None
    is_cb = False

    if update.message:
        uid = update.message.from_user.id
        is_cb = False
        metrics["messages"] += 1

    elif update.callback_query:
        uid = update.callback_query.from_user.id
        is_cb = True
        metrics["callbacks"] += 1

    # Anti-flood messages
    if uid and not is_cb:
        now = time.time()
        if now - last_msg.get(uid, 0) < RATE_LIMIT_MSG:
            return {"ok": True}
        last_msg[uid] = now

    # Anti-flood callbacks
    if uid and is_cb:
        now = time.time()
        if now - last_cb.get(uid, 0) < RATE_LIMIT_CB:
            return {"ok": True}
        last_cb[uid] = now

    # Skip old updates
    if update.message and update.message.date:
        if time.time() - update.message.date.timestamp() > MAX_UPDATE_DELAY:
            return {"ok": True}

    try:
        await dp.feed_update(bot, update)
    except TelegramBadRequest as e:
        metrics["errors"] += 1
        await notify_admin(str(e))
        print(f"[TG BAD REQUEST] {e}")
    except Exception as e:
        metrics["errors"] += 1
        await notify_admin(str(e))
        print(f"[UPDATE ERROR] {e}")

    return {"ok": True}


# ===== ROOT =====

@app.get("/")
def root():
    return {
        "status": "running",
        "webhook": WEBHOOK_URL
    }


# ===== HEALTH CHECKS =====

@app.get("/health/redis")
async def redis_health():
    try:
        await redis_client.set("health_test", "1", ex=5)
        return {"ok": True}
    except:
        return {"ok": False}


@app.get("/health/sheets")
async def sheets_health():
    try:
        s = connect_to_sheet()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/metrics")
def get_metrics():
    return {
        **metrics,
        "uptime": int(time.time() - metrics["start_time"])
    }


# ===== STARTUP =====

@app.on_event("startup")
async def on_startup():
    try:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        print(f"[WEBHOOK] Installed: {WEBHOOK_URL}")
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")

    # preload file_ids
    await preload_all_images(bot)
    print("[PRELOAD] All product images cached")


@app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except:
        pass
