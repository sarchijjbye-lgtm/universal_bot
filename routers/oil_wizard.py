# routers/oil_wizard.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

oil_router = Router()


# ===============================================================
# FSM — состояния
# ===============================================================
class OilWizard(StatesGroup):
    goals = State()
    lifestyle = State()
    digestion = State()
    stress = State()
    sleep = State()
    sex = State()
    result = State()
    chat = State()


# ===============================================================
# Мультиселект-клавиатура
# ===============================================================
def multiselect_kb(options: dict, selected: set, back_cb=None):
    kb = InlineKeyboardBuilder()

    for key, lbl in options.items():
        prefix = "🟩 " if key in selected else "⬜ "
        kb.button(text=prefix + lbl, callback_data=f"ms:{key}")

    if back_cb:
        kb.button(text="⬅️ Назад", callback_data=back_cb)

    kb.button(text="➡️ Готово", callback_data="ms:done")

    kb.adjust(1)
    return kb.as_markup()


# ===============================================================
# СТАРТ
# ===============================================================
@oil_router.message(lambda m: m.text and "подбор" in m.text.lower())
async def start_quiz(msg: types.Message, state: FSMContext):

    await state.clear()
    await state.set_state(OilWizard.goals)
    await state.update_data(goals=set())

    await msg.answer(
        "🧬 <b>Индивидуальный подбор масла</b>\n\n"
        "Выберите ваши основные цели:",
        reply_markup=multiselect_kb({
            "energy": "Энергия",
            "brain": "Фокус / Память",
            "immunity": "Иммунитет",
            "digestion": "Пищеварение",
            "skin": "Кожа / Волосы",
            "stress": "Стресс / Спокойствие",
            "weight": "Вес / Метаболизм",
        }, set())
    )


# ===============================================================
# GOALS
# ===============================================================
@oil_router.callback_query(OilWizard.goals)
async def cb_goals(cb: types.CallbackQuery, state: FSMContext):

    _, key = cb.data.split(":", 1)
    data = await state.get_data()
    selected = set(data["goals"])

    # Готово
    if key == "done":
        if not selected:
            return await cb.answer("Выберите хотя бы одну цель 🙏", show_alert=True)

        await state.set_state(OilWizard.lifestyle)
        await state.update_data(lifestyle=set())

        return await cb.message.edit_text(
            "🥗 <b>Как питаешься?</b>",
            reply_markup=multiselect_kb({
                "fat": "Много жирного",
                "sweet": "Сладкое",
                "fish_low": "Мало рыбы",
                "veg_low": "Мало овощей",
                "normal": "Обычное питание",
                "sport": "Спорт / ПП",
            }, set(), back_cb="back_goals")
        )

    # Переключение
    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(goals=selected)

    await cb.message.edit_reply_markup(
        multiselect_kb({
            "energy": "Энергия",
            "brain": "Фокус / Память",
            "immunity": "Иммунитет",
            "digestion": "Пищеварение",
            "skin": "Кожа / Волосы",
            "stress": "Стресс / Спокойствие",
            "weight": "Вес / Метаболизм",
        }, selected)
    )


@oil_router.callback_query(lambda c: c.data == "back_goals")
async def back_goals(cb, state):
    sel = (await state.get_data())["goals"]

    await state.set_state(OilWizard.goals)

    await cb.message.edit_text(
        "🧬 <b>Индивидуальный подбор масла</b>\nВыберите цели:",
        reply_markup=multiselect_kb({
            "energy": "Энергия",
            "brain": "Фокус / Память",
            "immunity": "Иммунитет",
            "digestion": "Пищеварение",
            "skin": "Кожа / Волосы",
            "stress": "Стресс / Спокойствие",
            "weight": "Вес / Метаболизм",
        }, sel)
    )


# ===============================================================
# LIFESTYLE
# ===============================================================
@oil_router.callback_query(OilWizard.lifestyle)
async def cb_lifestyle(cb, state):
    _, key = cb.data.split(":", 1)

    data = await state.get_data()
    selected = set(data["lifestyle"])

    if key == "done":
        await state.set_state(OilWizard.digestion)

        kb = InlineKeyboardBuilder()
        kb.button(text="👍 Всё хорошо", callback_data="dig:ok")
        kb.button(text="😐 Иногда тяжесть", callback_data="dig:mid")
        kb.button(text="😣 Часто вздутие", callback_data="dig:bad")
        kb.button(text="⬅️ Назад", callback_data="back_lifestyle")
        kb.adjust(1)

        return await cb.message.edit_text(
            "🍏 <b>Пищеварение</b>:", reply_markup=kb.as_markup()
        )

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(lifestyle=selected)

    await cb.message.edit_reply_markup(
        multiselect_kb({
            "fat": "Много жирного",
            "sweet": "Сладкое",
            "fish_low": "Мало рыбы",
            "veg_low": "Мало овощей",
            "normal": "Обычное питание",
            "sport": "Спорт / ПП",
        }, selected, back_cb="back_goals")
    )


@oil_router.callback_query(lambda c: c.data == "back_lifestyle")
async def back_lifestyle(cb, state):

    selected = (await state.get_data())["lifestyle"]

    await state.set_state(OilWizard.lifestyle)

    await cb.message.edit_text(
        "🥗 <b>Как питаешься?</b>",
        reply_markup=multiselect_kb({
            "fat": "Много жирного",
            "sweet": "Сладкое",
            "fish_low": "Мало рыбы",
            "veg_low": "Мало овощей",
            "normal": "Обычное питание",
            "sport": "Спорт / ПП",
        }, selected, back_cb="back_goals")
    )


# ===============================================================
# DIGESTION
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("dig:"))
async def cb_digestion(cb, state):

    _, val = cb.data.split(":", 1)

    if val == "back":
        return

    await state.update_data(digestion=val)
    await state.set_state(OilWizard.stress)

    kb = InlineKeyboardBuilder()
    kb.button(text="Редко", callback_data="stress:low")
    kb.button(text="Иногда", callback_data="stress:mid")
    kb.button(text="Часто", callback_data="stress:high")
    kb.button(text="⬅️ Назад", callback_data="back_digestion")
    kb.adjust(1)

    await cb.message.edit_text("😌 <b>Как часто стресс?</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back_digestion")
async def back_digestion(cb, state):

    await state.set_state(OilWizard.digestion)

    kb = InlineKeyboardBuilder()
    kb.button(text="👍 Всё хорошо", callback_data="dig:ok")
    kb.button(text="😐 Иногда тяжесть", callback_data="dig:mid")
    kb.button(text="😣 Часто вздутие", callback_data="dig:bad")
    kb.button(text="⬅️ Назад", callback_data="back_lifestyle")
    kb.adjust(1)

    await cb.message.edit_text("🍏 <b>Пищеварение</b>:", reply_markup=kb.as_markup())


# ===============================================================
# STRESS
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("stress:"))
async def cb_stress(cb, state):

    _, val = cb.data.split(":", 1)
    await state.update_data(stress=val)
    await state.set_state(OilWizard.sleep)

    kb = InlineKeyboardBuilder()
    kb.button(text="Хороший", callback_data="sleep:good")
    kb.button(text="Средний", callback_data="sleep:mid")
    kb.button(text="Плохой", callback_data="sleep:bad")
    kb.button(text="⬅️ Назад", callback_data="back_stress")
    kb.adjust(1)

    await cb.message.edit_text("🌙 <b>Как спишь?</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back_stress")
async def back_stress(cb, state):

    await state.set_state(OilWizard.stress)

    kb = InlineKeyboardBuilder()
    kb.button(text="Редко", callback_data="stress:low")
    kb.button(text="Иногда", callback_data="stress:mid")
    kb.button(text="Часто", callback_data="stress:high")
    kb.button(text="⬅️ Назад", callback_data="back_digestion")
    kb.adjust(1)

    await cb.message.edit_text("😌 <b>Как часто стресс?</b>", reply_markup=kb.as_markup())


# ===============================================================
# SLEEP
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("sleep:"))
async def cb_sleep(cb, state):
    _, val = cb.data.split(":", 1)

    await state.update_data(sleep=val)
    await state.set_state(OilWizard.sex)

    kb = InlineKeyboardBuilder()
    kb.button(text="Мужской", callback_data="sex:m")
    kb.button(text="Женский", callback_data="sex:f")
    kb.button(text="⬅️ Назад", callback_data="back_sleep")
    kb.adjust(1)

    await cb.message.edit_text("🧬 <b>Пол:</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back_sleep")
async def back_sleep(cb, state):

    await state.set_state(OilWizard.sleep)

    kb = InlineKeyboardBuilder()
    kb.button(text="Хороший", callback_data="sleep:good")
    kb.button(text="Средний", callback_data="sleep:mid")
    kb.button(text="Плохой", callback_data="sleep:bad")
    kb.button(text="⬅️ Назад", callback_data="back_stress")
    kb.adjust(1)

    await cb.message.edit_text("🌙 <b>Как спишь?</b>", reply_markup=kb.as_markup())


# ===============================================================
# SEX → RESULT
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("sex:"))
async def cb_sex(cb, state):

    _, s = cb.data.split(":", 1)
    await state.update_data(sex=s)

    await finish_recommendation(cb, state)


# ===============================================================
# ENGINE
# ===============================================================
async def finish_recommendation(cb, state):

    data = await state.get_data()
    await state.clear()

    products = load_products_safe()

    score = {pid: 0 for pid in ["1", "4", "7", "10", "13", "16", "19"]}

    g = data["goals"]

    # цели
    if "brain" in g: score["7"] += 3
    if "energy" in g: score["7"] += 2
    if "stress" in g: score["10"] += 2; score["7"] += 1
    if "digestion" in g: score["4"] += 2; score["13"] += 1
    if "immunity" in g: score["13"] += 3; score["10"] += 1
    if "skin" in g: score["1"] += 2; score["16"] += 1
    if "weight" in g: score["1"] += 3

    # пищеварение
    if data["digestion"] == "bad": score["4"] += 3
    if data["digestion"] == "mid": score["10"] += 1

    # стресс
    if data["stress"] == "high": score["13"] += 3
    if data["stress"] == "mid": score["10"] += 1

    # сон
    if data["sleep"] == "bad": score["13"] += 2
    if data["sleep"] == "mid": score["10"] += 1

    best = max(score, key=score.get)

    name = next(p["name"] for p in products if p["id"] == best)

    explanations = {
        "1": "Помогает гормональному балансу, коже и метаболизму.",
        "4": "Поддерживает пищеварение, печень и снижает воспаление.",
        "7": "Улучшает фокус, память и нервную систему.",
        "10": "Баланс Омега-3/6 снижает тревожность.",
        "13": "Сильный иммунитет + стресс-резистентность.",
        "16": "Поддержка кожи, энергии и ЖКТ.",
        "19": "Универсальное базовое масло для всех.",
    }

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Выбрать объём", callback_data=f"prod:{best}")
    kb.button(text="💬 Консультация", callback_data=f"chat:start:{best}")
    kb.adjust(1)

    await cb.message.edit_text(
        f"🌿 <b>Ваше персональное масло</b>\n\n"
        f"<b>{name}</b>\n{explanations[best]}\n\n"
        f"Что дальше?",
        reply_markup=kb.as_markup()
    )


# ===============================================================
# CONSULTATION CHAT
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("chat:start:"))
async def cb_chat_start(cb, state):
    pid = cb.data.split(":")[2]
    await state.set_state(OilWizard.chat)
    await state.update_data(product_id=pid)

    await cb.message.edit_text(
        "💬 <b>Консультация</b>\nСпроси о применении или противопоказаниях."
    )


@oil_router.message(OilWizard.chat)
async def cb_chat(msg, state):
    pid = (await state.get_data()).get("product_id")

    NAMES = {
        "1": "Льняное масло",
        "4": "Тыквенное масло",
        "7": "Масло грецкого ореха",
        "10": "Масло конопляное",
        "13": "Масло чёрного тмина",
        "16": "Масло кокосовое",
        "19": "Масло подсолнечное",
    }

    name = NAMES.get(pid, "Масло")

    await msg.answer(
        f"🧬 <b>{name}</b>\n\n"
        "• 1 ч.л. утром за 30 мин до еды\n"
        "• Курс 30–45 дней\n"
        "• Можно добавлять в салаты\n"
        "• Не жарить — теряются Омега-жиры\n"
        "• При чувствительном ЖКТ — начать с 1/2 ч.л.\n\n"
        "Готов ответить на уточняющие вопросы 😊"
    )
