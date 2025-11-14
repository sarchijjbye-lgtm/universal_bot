# utils/files.py

from google_sheets import load_products
from caching import cache_set
import json

async def preload_all_images(bot):
    """
    Подгружает все фото товаров в Telegram FileStorage.
    Если фото локальные — отправляет, затем сохраняет file_id.
    """

    try:
        products = load_products()
    except Exception as e:
        print("[PRELOAD ERROR]", e)
        return

    for product in products:
        key = f"fileid:{product['id']}"
        if product.get("file_id"):
            await cache_set(key, product["file_id"], ttl=86400)
            continue

        try:
            msg = await bot.send_photo(
                chat_id=product["debug_chat_id"],
                photo=product["photo_url"],
                caption="preload"
            )

            file_id = msg.photo[-1].file_id
            await cache_set(key, file_id)

        except Exception as e:
            print(f"[PRELOAD FAIL] {product['name']}: {e}")
