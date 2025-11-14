# routers/catalog.py
from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from utils.sheets import load_products

catalog_router = Router()

# === КЕШ ПРОДУКТОВ ===
PRODUCTS_CACHE: list[dict] | None = None

# Сколько товаров показывать на одной странице категории
ITEMS_PER_PAGE = 5


def normalize_variants(products: list[dict]) -> None:
    """
    Приводим variants к единому формату:
    [{"id": "...", "name": "...", "price": 123}]
    """
    for p in products:
        variants = p.get("variants")
        if isinstance(variants, list):
            for v in variants:
                # иногда вместо name приходит label — исправляем
                if "name" not in v and "label" in v:
                    v["name"] = v["label"]
                    del v["label"]


def get_products(force_reload: bool = False) -> list[dict]:
    """
    Загружаем продукты из Google Sheets с кешированием и фолбэком.
    """
    global PRODUCTS_CACHE

    # Если уже загружали и не просили принудительный reload — отдаем из кеша
    if PRODUCTS_CACHE is not None and not force_reload:
        return PRODUCTS_CACHE

    try:
        print("[CATALOG] Loading products from Google Sheets...")
        products = load_products() or []
        normalize_variants(products)
        PRODUCTS_CACHE = products
        print(f"[CATALOG] Loaded {len(PRODUCTS_CACHE)} items")
    except Exception as e:
        print(f"[CATALOG] ERROR loading products: {e}")
        # Если произошла ошибка, но в кеше что-то уже было — не падаем
        if PRODUCTS_CACHE is not None:
            print("[CATALOG] Using cached products due to error.")
        else:
            PRODUCTS_CACHE = []

    return PRODUCTS_CACHE


def build_category_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """
    Клавиатура категорий.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"cat_{c}_p1")]
            for c in categories
        ]
    )


def build_items_keyboard(cat: str, items: list[dict], page: int) -> InlineKeyboardMarkup:
    """
    Клавиатура товаров + кнопки пагинации.
    """
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = items[start:end]

    kb_rows: list[list[InlineKeyboardButton]] = []

    # Кнопки товаров
    for p in page_items:
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=p["name"],
                    callback_data=f"item_{p['id']}"
                )
            ]
        )

    # Пагинация
    nav_row: list[InlineKeyboardButton] = []

    if start > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"cat_{cat}_p{page - 1}",
            )
        )

    if end < len(items):
        nav_row.append(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data=f"cat_{cat}_p{page + 1}",
            )
        )

    if nav_row:
        kb_rows.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


def get_photo_ref(product: dict) -> str | None:
    """
    Возвращаем корректное значение для photo:
    - если в таблице лежит file_id → возвращаем его
    - если там http/https URL → возвращаем URL
    - иначе возвращаем None (будем слать только текст)
    """
    ref = (product.get("photo_url") or "").strip()

    if not ref:
        return None

    # Очень грубая, но рабочая эвристика:
    # - если начинается с http — считаем URL
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref

    # file_id обычно длинный, содержит буквы/цифры/подчеркивания/дефисы,
    # часто начинается с AgAC..., CQAC..., и т.п.
    # Для нас достаточно просто вернуть строку как есть —
    # Telegram сам поймёт, что это file_id.
    if len(ref) > 20:
        return ref

    # Всё остальное считаем мусором
    return None


# ================== HANDLERS ==================


@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(message: types.Message):
    """
    Старт каталога: показываем список категорий.
    """
    products = get_products()
    categories = sorted(list({p["category"] for p in products if p.get("category")}))

    if not categories:
        await message.answer("Каталог пока пуст 😔")
        return

    kb = build_category_keyboard(categories)
    await message.answer("Выберите категорию:", reply_markup=kb)


@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery):
    """
    Показ товаров категории с пагинацией: cat_<category>_p<page>
    """
    data = callback.data  # типа "cat_Масла_p1"
    payload = data[4:]    # "Масла_p1"
    if "_p" in payload:
        cat, page_str = payload.rsplit("_p", 1)
        try:
            page = int(page_str)
        except ValueError:
            page = 1
    else:
        cat = payload
        page = 1

    products = get_products()
    items = [p for p in products if p.get("category") == cat]

    if not items:
        await callback.message.edit_text(f"В категории <b>{cat}</b> пока нет товаров 😔", parse_mode="HTML")
        await callback.answer()
        return

    kb = build_items_keyboard(cat, items, page)
    text = f"Категория: <b>{cat}</b>\nСтраница {page} из {(len(items) - 1) // ITEMS_PER_PAGE + 1}"

    # Лучше редактировать сообщение, а не слать новое
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    # callback.answer() может иногда падать, если callback просрочен — завернём в try
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


@catalog_router.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(callback: types.CallbackQuery):
    """
    Красивая карточка товара с вариантами.
    """
    products = get_products()
    item_id = callback.data[5:]

    product = next((x for x in products if str(x.get("id")) == item_id), None)

    if not product:
        await callback.message.answer("Ошибка: товар не найден 😔")
        try:
            await callback.answer()
        except TelegramBadRequest:
            pass
        return

    name = product.get("name", "Без названия")
    desc = product.get("description", "Описание скоро появится")
    base_price = product.get("base_price") or 0

    # --- текст карточки (чуть красивее) ---
    text_lines = [
        f"<b>📦 {name}</b>",
        "",
        f"{desc}",
        "",
    ]

    if product.get("variants"):
        text_lines.append("<b>Доступные объёмы:</b>")
        for v in product["variants"]:
            text_lines.append(f"• {v['name']} — <b>{v['price']} ₽</b>")
    else:
        if base_price:
            text_lines.append(f"<b>Цена:</b> {base_price} ₽")

    text_lines.append("")
    text_lines.append("Выберите объём / вариант ниже 👇")

    text = "\n".join(text_lines)

    # --- фото ---
    photo_ref = get_photo_ref(product)

    # --- кнопки вариантов ---
    ikb: list[list[InlineKeyboardButton]] = []

    if product.get("variants"):
        for v in product["variants"]:
            ikb.append(
                [
                    InlineKeyboardButton(
                        text=f"{v['name']} — {v['price']} ₽",
                        callback_data=f"add_{product['id']}_{v['id']}",
                    )
                ]
            )
    else:
        ikb.append(
            [
                InlineKeyboardButton(
                    text=f"Добавить — {base_price} ₽",
                    callback_data=f"add_{product['id']}_base",
                )
            ]
        )

    kb = InlineKeyboardMarkup(inline_keyboard=ikb)

    # --- отправляем карточку ---
    try:
        if photo_ref:
            await callback.message.answer_photo(
                photo=photo_ref,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            # Если нет фото — просто текст
            await callback.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=kb,
            )

    except TelegramBadRequest as e:
        # Если картинка всё равно не зашла (битый URL и т.п.) — fallback на текст
        print(f"[CATALOG] Error sending photo for product {product.get('id')}: {e}")
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
        )

    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
