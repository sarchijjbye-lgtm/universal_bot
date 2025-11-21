# routers/ai_assistant.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from google_sheets import load_products_safe

ai_router = Router()


# ============================================================
# FSM STATES
# ============================================================

class OilQuiz(StatesGroup):
    start = State()
    goals = State()
    lifestyle = State()
    allergies = State()
    activity = State()
    age = State()
    sex = State()
    adaptive = State()
    result = State()


# ============================================================
# INLINE MULTISELECT BUTTON BUILDER
# ============================================================

def multiselect_keyboard(options: dict, selected: set, done_label="Готово"):
    kb = InlineKeyboardBuilder()

    for key, label in options.items():
        txt = ("🟩 " if key in selected else "⬜ ") + label
        kb.button(text=txt, callback_data=f"ms:{key}")
    kb.button(text=f"➡️ {done_label}", callback_data="ms:done")
    kb.adjust(1)
    return kb.as_markup()


# ============================================================
# START MENU BUTTON
# ============================================================

@ai_router.message(lambda m: m.text in ["🧬 Подбор масла", "🧬 Идеальный подбор масла"])
async def ai_start(msg: types.Message, state: FSMContext):
    await state.set_state(OilQuiz.start)

    await msg.answer(
        "👋 <b>Привет!</b>\n"
        "Я помогу подобрать идеальное сыродавленное масло под твой организм.\n\n"
        "Это как короткая консультация у нутрициолога — всего 6–7 вопросов.\n\n"
        "Готов начать?",
        reply_markup=InlineKeyboardBuilder()
            .button(text="Да, начать", callback_data="quiz:start")
            .button(text="Нет, позже", callback_data="quiz:cancel")
            .adjust(1)
            .as_markup()
    )


@ai_router.callback_query(lambda c: c.data == "quiz:cancel")
async def cancel_quiz(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Хорошо! Если что — я рядом 😊")
    await cb.answer()


# ============================================================
# QUESTION 1 — GOALS
# ============================================================

GOAL_OPTIONS = {
    "energy": "Энергия и работоспособность",
    "brain": "Память и концентрация",
    "immunity": "Иммунитет",
    "digestion": "ЖКТ и пищеварение",
    "skin": "Кожа и волосы",
    "stress": "Стресс и сон",
    "weight": "Обмен веществ / похудение",
    "male": "Мужское здоровье",
    "female": "Женское здоровье",
}


@ai_router.callback_query(lambda c: c.data == "quiz:start")
async def q1_goals(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(OilQuiz.goals)
    await state.update_data(goals=set())

    await cb.message.edit_text(
        "🧠 <b>С какими задачами хочешь поработать?</b>\n"
        "Можно выбрать несколько.",
        reply_markup=multiselect_keyboard(GOAL_OPTIONS, set())
    )
    await cb.answer()


@ai_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.reply_markup and "Готово" in c.message.reply_markup.inline_keyboard[-1][0].text)
async def q1_handler(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("goals", set())

    key = cb.data.split(":")[1]
    if key == "done":
        if not selected:
            return await cb.answer("Выберите хотя бы одну цель", show_alert=True)

        # переход к следующему вопросу
        await state.set_state(OilQuiz.lifestyle)
        await state.update_data(lifestyle=set())

        await cb.message.edit_text(
            "🥗 <b>Как питаешься обычно?</b>\nМожно выбрать несколько.",
            reply_markup=multiselect_keyboard({
                "fat": "Много жирного / фастфуда",
                "sweet": "Много сладкого",
                "fish_low": "Мало рыбы",
                "veg_low": "Мало овощей",
                "normal": "Обычное питание",
                "sport": "Занимаюсь спортом"
            }, set())
        )
        return

    # toggle
    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(goals=selected)
    await cb.message.edit_reply_markup(
        multiselect_keyboard(GOAL_OPTIONS, selected)
    )
    await cb.answer()


# ============================================================
# QUESTION 2 — LIFESTYLE
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.text.startswith("🥗"))
async def q2_handler(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("lifestyle", set())

    key = cb.data.split(":")[1]
    if key == "done":
        await state.set_state(OilQuiz.allergies)
        await state.update_data(allergies=set())

        await cb.message.edit_text(
            "😌 <b>Есть аллергии или ограничения?</b>",
            reply_markup=multiselect_keyboard({
                "nuts": "Орехи",
                "seeds": "Семечки",
                "sensitive": "Чувствительный желудок",
                "none": "Нет ограничений"
            }, set())
        )
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(lifestyle=selected)

    await cb.message.edit_reply_markup(
        multiselect_keyboard({
            "fat": "Много жирного / фастфуда",
            "sweet": "Много сладкого",
            "fish_low": "Мало рыбы",
            "veg_low": "Мало овощей",
            "normal": "Обычное питание",
            "sport": "Занимаюсь спортом"
        }, selected)
    )
    await cb.answer()


# ============================================================
# QUESTION 3 — ALLERGIES
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.text.startswith("😌"))
async def q3_handler(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("allergies", set())

    key = cb.data.split(":")[1]
    if key == "done":
        await state.set_state(OilQuiz.activity)

        kb = InlineKeyboardBuilder()
        kb.button(text="Низкая", callback_data="act:low")
        kb.button(text="Средняя", callback_data="act:mid")
        kb.button(text="Высокая", callback_data="act:high")
        kb.adjust(1)

        await cb.message.edit_text("⚡ <b>Какой образ жизни?</b>", reply_markup=kb.as_markup())
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(allergies=selected)

    await cb.message.edit_reply_markup(
        multiselect_keyboard({
            "nuts": "Орехи",
            "seeds": "Семечки",
            "sensitive": "Чувствительный желудок",
            "none": "Нет ограничений"
        }, selected)
    )
    await cb.answer()


# ============================================================
# QUESTION 4 — ACTIVITY
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("act:"))
async def q4_activity(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(activity=cb.data.split(":")[1])

    kb = InlineKeyboardBuilder()
    kb.button(text="16–25", callback_data="age:16")
    kb.button(text="26–40", callback_data="age:26")
    kb.button(text="40–55", callback_data="age:40")
    kb.button(text="55+", callback_data="age:55")
    kb.adjust(1)

    await state.set_state(OilQuiz.age)
    await cb.message.edit_text("🎯 <b>Возраст:</b>", reply_markup=kb.as_markup())
    await cb.answer()


# ============================================================
# QUESTION 5 — AGE
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("age:"))
async def q5_age(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(age=cb.data.split(":")[1])

    kb = InlineKeyboardBuilder()
    kb.button(text="Мужской", callback_data="sex:m")
    kb.button(text="Женский", callback_data="sex:f")
    kb.adjust(1)

    await state.set_state(OilQuiz.sex)
    await cb.message.edit_text("🧬 <b>Пол:</b>", reply_markup=kb.as_markup())
    await cb.answer()


# ============================================================
# QUESTION 6 — SEX (and adaptive question)
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("sex:"))
async def q6_sex(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(sex=cb.data.split(":")[1])

    data = await state.get_data()

    # адаптивный вопрос
    if "brain" in data["goals"]:
        kb = InlineKeyboardBuilder()
        kb.button(text="Почти постоянно", callback_data="extra:high")
        kb.button(text="Иногда", callback_data="extra:mid")
        kb.button(text="Редко", callback_data="extra:low")
        kb.adjust(1)

        question = "🧠 Как часто чувствуешь умственную усталость?"

    elif "digestion" in data["goals"]:
        kb = InlineKeyboardBuilder()
        kb.button(text="Да", callback_data="extra:yes")
        kb.button(text="Иногда", callback_data="extra:mid")
        kb.button(text="Нет", callback_data="extra:no")
        kb.adjust(1)

        question = "🍏 Бывает ли вздутие или тяжесть?"

    else:
        await finish_recommendation(cb, state)
        return

    await state.set_state(OilQuiz.adaptive)
    await cb.message.edit_text(question, reply_markup=kb.as_markup())


# ============================================================
# ADAPTIVE HANDLER
# ============================================================

@ai_router.callback_query(lambda c: c.data.startswith("extra:"))
async def q7_extra(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(extra=cb.data.split(":")[1])
    await finish_recommendation(cb, state)


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

async def finish_recommendation(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    products = load_products_safe()

    # MATCHING
    # простой, но эффективный медицинский алгоритм

    score = {
        "1": 0,   # льняное
        "4": 0,   # тыквенное
        "7": 0    # грецкое
    }

    # ENERGY
    if "energy" in data["goals"]:
        score["7"] += 2
        score["1"] += 1

    # BRAIN
    if "brain" in data["goals"]:
        score["7"] += 3
        score["1"] += 1

    # IMMUNITY
    if "immunity" in data["goals"]:
        score["4"] += 2
        score["7"] += 1

    # DIGESTION
    if "digestion" in data["goals"]:
        score["4"] += 3

    # SKIN
    if "skin" in data["goals"]:
        score["1"] += 2
        score["7"] += 1

    # STRESS
    if "stress" in data["goals"]:
        score["7"] += 2

    # WEIGHT
    if "weight" in data["goals"]:
        score["1"] += 3

    # MALE
    if "male" in data["goals"]:
        score["4"] += 3

    # FEMALE
    if "female" in data["goals"]:
        score["1"] += 1
        score["7"] += 1

    # ALLERGIES
    if "nuts" in data.get("allergies", []):
        score["7"] -= 999  # орех нельзя

    if "seeds" in data.get("allergies", []):
        score["1"] -= 999
        score["4"] -= 999

    # EXTRA ADAPTIVE
    if data.get("extra") == "high":
        score["7"] += 2

    if data.get("extra") == "yes":
        score["4"] += 2

    recommended = max(score, key=score.get)
    product_id = recommended

    # текстовая интерпретация
    explanations = {
        "1": "Сильный источник Омега-3, улучшает обмен веществ, кожу и гормональный баланс.",
        "4": "Мощная поддержка печени, иммунитета, мужского здоровья и пищеварения.",
        "7": "Лучшее масло для мозга, концентрации, энергии и нервной системы."
    }

    name = next(p["name"] for p in products if p["id"] == product_id)

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Выбрать объём", callback_data=f"prod:{product_id}")
    kb.adjust(1)

    await cb.message.edit_text(
        f"🌿 <b>Твоя персональная рекомендация</b>\n\n"
        f"<b>{name}</b>\n{explanations[product_id]}\n\n"
        f"👇 Выбери объём:",
        reply_markup=kb.as_markup()
    )
    await cb.answer()
