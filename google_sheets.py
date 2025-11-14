# google_sheets.py
"""
Модуль работы с Google Sheets для HION бота.

Функции:
- load_products_safe(...) — безопасная асинхронная загрузка каталога с кэшированием.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional

import gspread

from caching import cache_get, cache_set


# === НАСТРОЙКИ ===
# ID таблицы Google Sheets (можно хранить в .env / Render env)
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
# Имя листа с товарами
GOOGLE_SHEETS_PRODUCTS_SHEET = os.getenv("GOOGLE_SHEETS_PRODUCTS_SHEET", "Products")
# TTL кэша в секундах (5 минут)
DEFAULT_PRODUCTS_TTL = int(os.getenv("PRODUCTS_CACHE_TTL", "300"))

# Переменная для клиента, чтобы не создавать его каждый раз
_gs_client: Optional[gspread.Client] = None


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _get_gspread_client() -> gspread.Client:
    """
    Инициализация клиента Google Sheets.
    Ожидает, что в переменной окружения GOOGLE_SERVICE_ACCOUNT_JSON лежит
    JSON сервисного аккаунта (как строка).
    """
    global _gs_client
    if _gs_client is not None:
        return _gs_client

    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set in environment. "
            "Put service account JSON there as one-line string."
        )

    try:
        creds_dict = json.loads(creds_json)
    except json.JSONDecodeError:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")

    _gs_client = gspread.service_account_from_dict(creds_dict)
    return _gs_client


def _parse_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводим строку из Sheets к нормальному виду.
    Ожидаемые поля:
    id, category, name, description, base_price, variants, photo_url, active
    """
    # ID всегда строкой
    pid = str(row.get("id") or "").strip()

    # variants — строка с JSON
    variants_raw = row.get("variants") or ""
    variants: List[Dict[str, Any]] = []
    if variants_raw:
        try:
            variants = json.loads(variants_raw)
        except Exception as e:
            print("[GSHEETS] Error parsing variants JSON:", e, "raw:", variants_raw)

    # active — TRUE/FALSE
    active_raw = str(row.get("active") or "").strip().upper()
    active = active_raw in ("TRUE", "1", "YES", "Y", "ДА")

    base_price_str = str(row.get("base_price") or "0").strip()
    try:
        base_price = int(base_price_str)
    except ValueError:
        base_price = 0

    return {
        "id": pid,
        "category": str(row.get("category") or "").strip(),
        "name": str(row.get("name") or "").strip(),
        "description": str(row.get("description") or "").strip(),
        "base_price": base_price,
        "variants": variants,
        "photo_url": str(row.get("photo_url") or "").strip(),
        "active": active,
    }


def _load_products_sync() -> List[Dict[str, Any]]:
    """
    Синхронная загрузка товаров из Google Sheets.
    Вызывается через asyncio.to_thread из async wrapper'а.
    """
    if not GOOGLE_SHEETS_ID:
        raise RuntimeError("GOOGLE_SHEETS_ID is not set")

    client = _get_gspread_client()
    sheet = client.open_by_key(GOOGLE_SHEETS_ID)
    ws = sheet.worksheet(GOOGLE_SHEETS_PRODUCTS_SHEET)

    # Получаем все строки как dict
    rows = ws.get_all_records()
    products: List[Dict[str, Any]] = []

    for row in rows:
        product = _parse_row(row)
        if product["id"] and product["name"] and product["active"]:
            products.append(product)

    print(f"[GSHEETS] Loaded {len(products)} products from sheet.")
    return products


# === ПУБЛИЧНАЯ ОБЁРТКА ===

async def load_products_safe(*args, ttl: int = DEFAULT_PRODUCTS_TTL, **kwargs) -> List[Dict[str, Any]]:
    """
    Асинхронная безопасная загрузка каталога.

    - сначала пытается взять из Redis-кэша по ключу "products";
    - если в кэше нет — читает из Google Sheets в отдельном потоке;
    - складывает в кэш на ttl секунд;
    - при любой ошибке возвращает [] и печатает ошибку в лог.

    *args, **kwargs оставлены специально, чтобы не падать,
    даже если роутеры вызывают load_products_safe с какими-то параметрами.
    """
    cache_key = "products"

    # 1. Пробуем кэш
    try:
        cached = await cache_get(cache_key)
        if cached:
            try:
                products = json.loads(cached)
                # print(f"[CACHE] Products from cache: {len(products)}")
                return products
            except Exception as e:
                print("[CACHE] Error parsing cached products JSON:", e)
    except Exception as e:
        print("[CACHE] Error on cache_get:", e)

    # 2. Грузим из Google Sheets
    try:
        products = await asyncio.to_thread(_load_products_sync)
    except Exception as e:
        print("[GSHEETS] Error loading products:", e)
        return []

    # 3. Пишем в кэш
    try:
        await cache_set(cache_key, json.dumps(products, ensure_ascii=False), ttl)
    except Exception as e:
        print("[CACHE] Error on cache_set:", e)

    return products
