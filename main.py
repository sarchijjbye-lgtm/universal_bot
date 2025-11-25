import os
import asyncio
import datetime
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery
)

from google_sheets import (
    connect_to_sheet, add_order, get_orders, 
    load_products, update_product_photo
)
from config import BOT_TOKEN, ADMIN_CHAT_ID, GROUP_CHAT_ID

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

BOT_URL = os.getenv("BOT_URL", "https://hion-shop-bot.onrender.com")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = f"{BOT_URL}{WEBHOOK_PATH}"

# Главное меню
def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🌿 Каталог")],
        [KeyboardButton(text="🧩 Подбор масла"), KeyboardButton(text="🛒 Корзина")]
    ])
    return kb

# Данные
user_carts = {}
pending_address = {}
pending_phone = {}
user_profiles = {}
user_quiz = {}
admin_waiting_photo = {}

# Google Sheets
spreadsheet = connect_to_sheet()
products_cache = []

def refresh_products():
    """Обновить кэш товаров из Google Sheets"""
    global products_cache
    products_cache = load_products(spreadsheet)
    print(f"🔄 Кэш обновлён: {len(products_cache)} товаров")

refresh_products()

# === Структура каталога ===

def get_categories():
    """Получить список уникальных категорий"""
    categories = {}
    for p in products_cache:
        if not p["parent_id"]:
            cat = p["category"]
            if cat not in categories:
                categories[cat] = {
                    "id": p["id"],
                    "name": p["name"],
                    "description": p["description"],
                    "file_id": p["file_id"]
                }
    return categories

def get_products_by_parent(parent_id):
    return [p for p in products_cache if p["parent_id"] == str(parent_id)]

def get_product_by_id(product_id):
    for p in products_cache:
        if p["id"] == str(product_id):
            return p
    return None

# === Flask Routes ===

@app.route('/')
def home():
    return "✅ HION Bot is running with Google Sheets catalog."

@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook():
    try:
        update_data = request.get_json(force=True)
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
    return "OK", 200

@app.route('/remind')
async def remind_users():
    try:
        orders = get_orders(spreadsheet)
        today = datetime.datetime.now().date()
        
        for order in orders:
            if "@" not in order["Клиент"]:
                continue
            
            date_str = order["Время"].split(" ")[0]
            order_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if (today - order_date).days == 30:
                await bot.send_message(order["Клиент"], "🌿 Как вам масло? Пора обновить курс 💛")
        
        return "Reminders sent", 200
    except Exception as e:
        print(f"❌ Reminder error: {e}")
        return str(e), 500

@app.route('/refresh')
def refresh_catalog():
    refresh_products()
    return f"✅ Каталог обновлён: {len(products_cache)} товаров", 200

# === Handlers ===

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Добро пожаловать в HION 🌿\n"
        "Натуральные масла холодного отжима — прямо от производителя.\n\n"
        "👇 Выберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text.lower().contains("каталог"))
async def open_catalog(message: Message):
    categories = get_categories()
    
    if not categories:
        await message.answer("⚠️ Каталог пуст. Обновите товары в Google Sheets.")
        return
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌿 {cat_data['name']}", callback_data=f"cat|{cat_data['id']}")]
        for cat_name, cat_data in categories.items()
    ])
    
    await message.answer("🌿 Выберите категорию:", reply_markup=markup)

@dp.callback_query(F.data.startswith("cat|"))
async def show_category(callback: CallbackQuery):
    cat_id = callback.data.split("|")[1]
    product = get_product_by_id(cat_id)
    
    if not product:
        await callback.answer("❌ Категория не найдена")
        return
    
    variants = get_products_by_parent(cat_id)
    text = f"*{product['name']}*\n\n{product['description']}"
    
    buttons = []
    for var in variants:
        if var["variant_label"] and var["price"]:
            buttons.append([InlineKeyboardButton(
                text=f"{var['variant_label']} — {var['price']}₽",
                callback_data=f"add|{var['id']}|{var['variant_label']}|{var['price']}"
            )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="back_to_catalog")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if product["file_id"]:
        try:
            await callback.message.delete()
            await bot.send_photo(
                callback.from_user.id,
                photo=product["file_id"],
                caption=text,
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            print(f"⚠️ Ошибка отправки фото: {e}")
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    categories = get_categories()
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌿 {cat_data['name']}", callback_data=f"cat|{cat_data['id']}")]
        for cat_name, cat_data in categories.items()
    ])
    
    try:
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, "🌿 Выберите категорию:", reply_markup=markup)
    except:
        await callback.message.edit_text("🌿 Выберите категорию:", reply_markup=markup)

@dp.callback_query(F.data.startswith("add|"))
async def add_item(callback: CallbackQuery):
    _, product_id, variant, price = callback.data.split("|")
    user_id = callback.from_user.id
    
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("❌ Товар не найден")
        return
    
    user_carts.setdefault(user_id, []).append({
        "id": product_id,
        "name": product["name"],
        "variant": variant,
        "price": int(price)
    })
    
    await callback.answer("✅ Товар добавлен в корзину")
    await callback.message.answer(
        "🛒 Товар добавлен в корзину!\nОткройте её для оформления 💛",
        reply_markup=get_main_menu()
    )

async def send_cart(user_id, message_obj):
    cart = user_carts.get(user_id, [])
    
    if not cart:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌿 Вернуться в каталог", callback_data="back_to_catalog")]
        ])
        await message_obj.answer("🧺 Корзина пуста", reply_markup=markup)
        return
    
    total = sum(item["price"] for item in cart)
    text = "\n".join([f"{i+1}. {item['name']} {item['variant']} — {item['price']}₽" for i, item in enumerate(cart)])
    text += f"\n\n💰 Итого: {total}₽"
    
    buttons = [[InlineKeyboardButton(text=f"❌ Удалить {i+1}", callback_data=f"remove|{i}")] for i in range(len(cart))]
    buttons.append([InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")])
    buttons.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message_obj.answer(text, reply_markup=markup)

@dp.message(F.text.lower().contains("корзин"))
async def view_cart(message: Message):
    await send_cart(message.from_user.id, message)

@dp.callback_query(F.data.startswith("remove|"))
async def remove_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("|")[1])
    
    if user_id in user_carts and 0 <= index < len(user_carts[user_id]):
        user_carts[user_id].pop(index)
    
    await callback.message.delete()
    await send_cart(user_id, callback.message)

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_carts[callback.from_user.id] = []
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="back_to_catalog")]
    ])
    await callback.message.edit_text("🗑 Корзина очищена.", reply_markup=markup)

@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌿 Вернуться в каталог", callback_data="back_to_catalog")]
        ])
        await callback.message.edit_text("🧺 Корзина пуста.", reply_markup=markup)
        return
    
    text = (
        "🚚 Как удобнее получить заказ?\n\n"
        "💛 Стоимость доставки и адрес самовывоза "
        "согласовываются с менеджером после оформления.\n\n"
        "Выберите удобный способ ниже 👇"
    )
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Доставка", callback_data="delivery")],
        [InlineKeyboardButton(text="🏠 Самовывоз", callback_data="pickup")]
    ])
    
    await callback.message.edit_text(text, reply_markup=markup)

@dp.callback_query(F.data.in_(["delivery", "pickup"]))
async def choose_delivery(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "pickup":
        await ask_phone(callback.message, "Самовывоз — ул. Гостиева, 8")
    else:
        pending_address[user_id] = True
        await callback.message.edit_text("📍 Напишите адрес доставки (улица, дом, квартира) 💌:")

async def ask_phone(message, address):
    user_id = message.from_user.id
    pending_phone[user_id] = address
    
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[[KeyboardButton(text="📞 Отправить номер", request_contact=True)]]
    )
    
    await message.answer("📞 Укажите номер телефона для связи:", reply_markup=kb)

@dp.message(F.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    address = pending_phone.pop(user_id, "—")
    
    await finalize_order(message, address, phone)

async def finalize_order(message, address, phone):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    
    total = sum(item["price"] for item in cart)
    items = "; ".join([f"{item['name']} {item['variant']} — {item['price']}₽" for item in cart])
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    
    add_order(spreadsheet, username, items, address, total, phone)
    user_profiles[user_id] = {"address": address, "phone": phone}
    
    order_text = f"🛍 Новый заказ:\n{items}\n\n💰 {total}₽\n📍 {address}\n📞 {phone}\n👤 {username}"
    
    await bot.send_message(ADMIN_CHAT_ID, order_text)
    if GROUP_CHAT_ID:
        await bot.send_message(GROUP_CHAT_ID, order_text)
    
    user_carts[user_id] = []
    
    await message.answer(
        "Спасибо! Ваш заказ зарегистрирован 💛\n"
        "Менеджер свяжется с вами в течение дня для уточнения деталей ✨",
        reply_markup=get_main_menu()
    )

# === ПОДБОР МАСЛА ===

QUIZ_QUESTIONS = {
    1: ("Если бы вы могли улучшить одно состояние прямо сейчас — что бы это было?",
        ["💪 Энергия и бодрость", "🧘 Спокойствие и устойчивость", "🫀 Сердце и сосуды",
         "💆 Кожа и волосы", "🧠 Концентрация и память", "🌸 Гормональный баланс"]),
    2: ("Как вы чувствуете себя в последние недели?",
        ["😊 Всё стабильно", "😴 Часто устаю", "🥴 Есть тревожность или стресс", 
         "🤧 Бывают простуды", "🤕 Есть проблемы с пищеварением"]),
    3: ("Какой у вас ритм жизни?",
        ["🏃 Очень активный", "💻 Сидячая работа", "😌 Спокойный ритм", "🔥 Много стресса"]),
    4: ("Какие продукты чаще всего на вашем столе?",
        ["🍗 Мясо, рыба, яйца", "🥦 Овощи, крупы, бобовые", "🍕 Фастфуд или сладкое", 
         "🌿 В основном растительное питание"]),
    5: ("Какое масло вы бы хотели — по ощущениям?",
        ["🌰 С насыщенным ореховым вкусом", "💧 Нейтральное, лёгкое", 
         "🌶 Пряное и характерное", "✨ Универсальное — и внутрь, и наружно"]),
    6: ("Используете ли вы масла для ухода за кожей или волосами?",
        ["💆 Да, часто", "💅 Иногда", "🚫 Нет, только внутрь"]),
    7: ("Какую цель хотите достичь быстрее всего?",
        ["🌿 Улучшить самочувствие", "💆 Улучшить внешний вид", 
         "🔥 Повысить энергию", "🧘 Снизить стресс"])
}

OIL_RECOMMENDATIONS = {
    "flax": "Масло льняное",
    "hemp": "Масло конопляное",
    "pumpkin": "Масло тыквенное",
    "blackseed": "Масло черного тмина",
    "sunflower": "Масло подсолнечное",
    "walnut": "Масло грецкого ореха",
    "coconut": "Масло кокосовое"
}

async def start_quiz(message: Message):
    user_quiz[message.from_user.id] = {"step": 1, "answers": {}}
    await send_quiz_question(message, 1)

async def send_quiz_question(message, step):
    q_text, q_options = QUIZ_QUESTIONS[step]
    buttons = [[KeyboardButton(text=opt)] for opt in q_options]
    
    nav = []
    if step > 1:
        nav.append(KeyboardButton(text="🔙 Назад"))
    nav.append(KeyboardButton(text="❌ Выйти"))
    buttons.append(nav)
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    await message.answer(q_text, reply_markup=kb)

async def handle_quiz_answer(message: Message):
    uid = message.from_user.id
    data = user_quiz.get(uid, {"step": 1, "answers": {}})
    step = data["step"]
    
    data["answers"][f"q{step}"] = message.text
    
    next_step = step + 1
    if next_step in QUIZ_QUESTIONS:
        user_quiz[uid]["step"] = next_step
        await send_quiz_question(message, next_step)
    else:
        await recommend_oil(message, data["answers"])
        user_quiz.pop(uid, None)

async def recommend_oil(message: Message, answers):
    joined = " ".join(answers.values()).lower()
    
    score = {k: 0 for k in OIL_RECOMMENDATIONS}
    
    if "устал" in joined or "энерг" in joined: score["coconut"] += 3
    if "стресс" in joined or "тревож" in joined: score["hemp"] += 3
    if "кожа" in joined or "волос" in joined: score["sunflower"] += 3
    if "память" in joined or "мозг" in joined: score["walnut"] += 3
    if "сердце" in joined or "сосуд" in joined: score["flax"] += 3
    if "иммун" in joined or "простуд" in joined: score["blackseed"] += 3
    if "печен" in joined or "жкт" in joined: score["pumpkin"] += 3
    if "гормон" in joined: 
        score["hemp"] += 2
        score["pumpkin"] += 2
    
    best = max(score, key=score.get)
    recommended_name = OIL_RECOMMENDATIONS[best]
    
    recommended_product = None
    for p in products_cache:
        if recommended_name.lower() in p["name"].lower() and not p["parent_id"]:
            recommended_product = p
            break
    
    if not recommended_product:
        await message.answer(
            "✨ К сожалению, рекомендованное масло сейчас недоступно.\n"
            "Попробуйте открыть каталог 🌿",
            reply_markup=get_main_menu()
        )
        return
    
    oil_emoji = {
        "flax": "💧", "hemp": "🌿", "pumpkin": "🎃",
        "blackseed": "🌑", "sunflower": "🌻",
        "walnut": "🌰", "coconut": "🥥"
    }.get(best, "🌿")
    
    text = (
        f"✨ Мы нашли масло, которое подходит именно вам.\n\n"
        f"{oil_emoji} *{recommended_product['name']}*\n\n"
        f"{recommended_product['description']}\n\n"
        f"🌿 Рекомендуем начать с 1 ч.л. утром курсом 1–2 месяца.\n"
        f"💛 Вы можете добавить его в корзину или открыть каталог."
    )
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Посмотреть варианты", callback_data=f"cat|{recommended_product['id']}")],
        [InlineKeyboardButton(text="🌿 Весь каталог", callback_data="back_to_catalog")]
    ])
    
    if recommended_product["file_id"]:
        try:
            await bot.send_photo(
                message.from_user.id,
                photo=recommended_product["file_id"],
                caption=text,
                parse_mode="Markdown",
                reply_markup=markup
            )
        except:
            await message.answer(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=markup)

# === АДМИН ===

@dp.message(Command("updatephoto"))
async def admin_update_photo(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("📸 Отправьте фото товара.\nПосле этого я попрошу указать ID товара из таблицы.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    
    file_id = message.photo[-1].file_id
    admin_waiting_photo[message.from_user.id] = file_id
    
    await message.answer(
        f"✅ Фото получено!\nFile ID: `{file_id}`\n\n"
        f"Теперь отправьте ID товара из Google Sheets (например, `1` или `4`):",
        parse_mode="Markdown"
    )

# === Обработка текста ===

@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = (message.text or "").lower()
    
    # Админ ждёт ID товара
    if user_id in admin_waiting_photo:
        product_id = message.text.strip()
        file_id = admin_waiting_photo.pop(user_id, None)
        
        if not file_id:
            await message.answer("❌ Фото не найдено. Попробуйте заново: /updatephoto")
            return
        
        success = update_product_photo(spreadsheet, product_id, file_id)
        
        if success:
            refresh_products()
            await message.answer(
                f"✅ Фото для товара ID={product_id} успешно обновлено!\n"
                f"Кэш обновлён автоматически.",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                f"⚠️ Не удалось обновить фото для ID={product_id}.\n"
                f"Проверьте, что такой ID существует в таблице.",
                reply_markup=get_main_menu()
            )
        return
    
    if "подбор" in text:
        await start_quiz(message)
        return
    
    if text.startswith("❌") or "выйти" in text:
        user_quiz.pop(user_id, None)
        await message.answer("Вы вышли из подбора масел 🌿", reply_markup=get_main_menu())
        return
    
    if text.startswith("🔙") or "назад" in text:
        if user_id in user_quiz:
            step = user_quiz[user_id]["step"]
            if step > 1:
                user_quiz[user_id]["step"] -= 1
                await send_quiz_question(message, user_quiz[user_id]["step"])
            else:
                await message.answer("Это первый вопрос 🌿", reply_markup=get_main_menu())
        return
    
    if user_id in user_quiz:
        await handle_quiz_answer(message)
        return
    
    if user_id in pending_address:
        address = message.text.strip()
        pending_address.pop(user_id, None)
        await ask_phone(message, address)
        return

# === Запуск ===

async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")

if __name__ == "__main__":
    import threading
    
    async def run_bot():
        await on_startup()
        print("🚀 Bot is running with Google Sheets catalog")
        print(f"📦 Loaded {len(products_cache)} products")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def run_async_loop():
        loop.run_until_complete(run_bot())
    
    threading.Thread(target=run_async_loop, daemon=True).start()
    
    app.run(host="0.0.0.0", port=8080)
