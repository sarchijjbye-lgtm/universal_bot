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
    finish = State()
    chat = State()


# ===============================================================
# Мультиселект
# ===============================================================
def multiselect(options: dict, selected: set, back_cb=None):
    kb = InlineKeyboardBuilder()

    for key, label in options.items():
        prefix = "🟩 " if key in selected else "⬜ "
        kb.button(text=prefix + label, callback_data=f"ms:{key}")

    if back_cb:
        kb.button(text="⬅️ Назад", callback_data=back_cb)

    kb.button(text="➡️ Готово", callback_data="ms:done")
    kb.adjust(1)
    return kb.as_markup()


# ===============================================================
# Старт
# ===============================================================
@oil_router.message(lambda m: m.text and "подбор" in m.text.lower())
async def start_quiz(msg: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OilWizard.goals)
    await state.update_data(goals=set())

    await msg.answer(
        "🧬 <b>Индивидуальный подбор масла</b>\n\n"
        "Отвечу как интегративный нутрициолог.\n"
        "Выберите ваши основные цели:",
        reply_markup=multiselect({
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
@oil_router.callback_query(lambda c: c.data.startswith("ms:") and "цели" not in c.message.text.lower())
async def q_goals(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data["goals"])
    key = cb.data.split(":")[1]

    if key == "done":
        if not selected:
            return await cb.answer("Выберите хотя бы одну цель 🙏", show_alert=True)

        await state.set_state(OilWizard.lifestyle)
        await state.update_data(lifestyle=set())

        await cb.message.edit_text(
            "🥗 <b>Как питаешься?</b>\nВыберите несколько:",
            reply_markup=multiselect({
                "fat": "Много жирного",
                "sweet": "Сладкое",
                "fish_low": "Мало рыбы",
                "veg_low": "Мало овощей",
                "normal": "Обычное питание",
                "sport": "Спорт / ПП",
            }, set(), back_cb="back:goals")
        )
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(goals=selected)

    await cb.message.edit_reply_markup(multiselect({
        "energy": "Энергия",
        "brain": "Фокус / Память",
        "immunity": "Иммунитет",
        "digestion": "Пищеварение",
        "skin": "Кожа / Волосы",
        "stress": "Стресс / Спокойствие",
        "weight": "Вес / Метаболизм",
    }, selected))


@oil_router.callback_query(lambda c: c.data == "back:goals")
async def back_goals(cb, state):
    data = await state.get_data()
    sel = data["goals"]

    await state.set_state(OilWizard.goals)
    await cb.message.edit_text(
        "🧬 <b>Индивидуальный подбор масла</b>\nВыберите ваши цели:",
        reply_markup=multiselect({
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
@oil_router.callback_query(lambda c: c.data.startswith("ms:") and "питаешься" in c.message.text.lower())
async def q_lifestyle(cb, state):
    data = await state.get_data()
    selected = set(data["lifestyle"])
    key = cb.data.split(":")[1]

    if key == "done":
        await state.set_state(OilWizard.digestion)

        kb = InlineKeyboardBuilder()
        kb.button(text="👍 Всё хорошо", callback_data="dig:ok")
        kb.button(text="😐 Бывает тяжесть", callback_data="dig:mid")
        kb.button(text="😣 Часто вздутие", callback_data="dig:bad")
        kb.button(text="⬅️ Назад", callback_data="back:lifestyle")
        kb.adjust(1)

        await cb.message.edit_text(
            "🍏 <b>Как работает пищеварение?</b>",
            reply_markup=kb.as_markup()
        )
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(lifestyle=selected)

    await cb.message.edit_reply_markup(multiselect({
        "fat": "Много жирного",
        "sweet": "Сладкое",
        "fish_low": "Мало рыбы",
        "veg_low": "Мало овощей",
        "normal": "Обычное питание",
        "sport": "Спорт / ПП",
    }, selected, back_cb="back:goals"))


@oil_router.callback_query(lambda c: c.data == "back:lifestyle")
async def back_ls(cb, state):
    data = await state.get_data()

    await state.set_state(OilWizard.lifestyle)
    await cb.message.edit_text(
        "🥗 <b>Как питаешься?</b>",
        reply_markup=multiselect({
            "fat": "Много жирного",
            "sweet": "Сладкое",
            "fish_low": "Мало рыбы",
            "veg_low": "Мало овощей",
            "normal": "Обычное питание",
            "sport": "Спорт / ПП",
        }, set(data["lifestyle"]), back_cb="back:goals")
    )


# ===============================================================
# DIGESTION
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("dig:"))
async def q_dig(cb, state):
    await state.update_data(digestion=cb.data.split(":")[1])
    await state.set_state(OilWizard.stress)

    kb = InlineKeyboardBuilder()
    kb.button(text="Редко", callback_data="stress:low")
    kb.button(text="Иногда", callback_data="stress:mid")
    kb.button(text="Часто", callback_data="stress:high")
    kb.button(text="⬅️ Назад", callback_data="back:digestion")
    kb.adjust(1)

    await cb.message.edit_text("😌 <b>Как часто испытываешь стресс?</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back:digestion")
async def back_dig(cb, state):
    await state.set_state(OilWizard.digestion)

    kb = InlineKeyboardBuilder()
    kb.button(text="👍 Всё хорошо", callback_data="dig:ok")
    kb.button(text="😐 Бывает тяжесть", callback_data="dig:mid")
    kb.button(text="😣 Часто вздутие", callback_data="dig:bad")
    kb.button(text="⬅️ Назад", callback_data="back:lifestyle")
    kb.adjust(1)

    await cb.message.edit_text("🍏 <b>Как работает пищеварение?</b>", reply_markup=kb.as_markup())


# ===============================================================
# STRESS
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("stress:"))
async def q_stress(cb, state):
    await state.update_data(stress=cb.data.split(":")[1])
    await state.set_state(OilWizard.sleep)

    kb = InlineKeyboardBuilder()
    kb.button(text="Хороший", callback_data="sleep:good")
    kb.button(text="Средний", callback_data="sleep:mid")
    kb.button(text="Плохой", callback_data="sleep:bad")
    kb.button(text="⬅️ Назад", callback_data="back:stress")
    kb.adjust(1)

    await cb.message.edit_text("🌙 <b>Как спишь?</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back:stress")
async def back_stress(cb, state):
    await state.set_state(OilWizard.stress)

    kb = InlineKeyboardBuilder()
    kb.button(text="Редко", callback_data="stress:low")
    kb.button(text="Иногда", callback_data="stress:mid")
    kb.button(text="Часто", callback_data="stress:high")
    kb.button(text="⬅️ Назад", callback_data="back:digestion")
    kb.adjust(1)

    await cb.message.edit_text("😌 <b>Как часто испытываешь стресс?</b>", reply_markup=kb.as_markup())


# ===============================================================
# SLEEP → SEX → RESULT
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("sleep:"))
async def q_sleep(cb, state):
    await state.update_data(sleep=cb.data.split(":")[1])
    await state.set_state(OilWizard.sex)

    kb = InlineKeyboardBuilder()
    kb.button(text="Мужской", callback_data="sex:m")
    kb.button(text="Женский", callback_data="sex:f")
    kb.button(text="⬅️ Назад", callback_data="back:sleep")
    kb.adjust(1)

    await cb.message.edit_text("🧬 <b>Ваш пол?</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back:sleep")
async def back_sleep(cb, state):
    await state.set_state(OilWizard.sleep)

    kb = InlineKeyboardBuilder()
    kb.button(text="Хороший", callback_data="sleep:good")
    kb.button(text="Средний", callback_data="sleep:mid")
    kb.button(text="Плохой", callback_data="sleep:bad")
    kb.button(text="⬅️ Назад", callback_data="back:stress")
    kb.adjust(1)

    await cb.message.edit_text("🌙 <b>Как спишь?</b>", reply_markup=kb.as_markup())


# ===============================================================
# SEX → RESULT
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("sex:"))
async def q_sex(cb, state):
    await state.update_data(sex=cb.data.split(":")[1])
    await finish_recommendation(cb, state)


# ===============================================================
# ENGINE — AI подбор
# ===============================================================
async def finish_recommendation(cb, state):
    data = await state.get_data()
    await state.clear()

    products = load_products_safe()

    score = {
        "1": 0,
        "4": 0,
        "7": 0,
        "10": 0,
        "13": 0,
        "16": 0,
        "19": 0,
    }

    # Цели
    g = data["goals"]
    if "brain" in g: score["7"] += 3
    if "energy" in g: score["7"] += 2
    if "stress" in g: score["10"] += 2; score["7"] += 1
    if "digestion" in g: score["4"] += 2; score["13"] += 1
    if "immunity" in g: score["13"] += 3; score["10"] += 1
    if "skin" in g: score["1"] += 2; score["16"] += 1
    if "weight" in g: score["1"] += 3

    # ЖКТ
    dig = data["digestion"]
    if dig == "bad": score["4"] += 3
    if dig == "mid": score["10"] += 1

    # Стресс
    st = data["stress"]
    if st == "high": score["13"] += 3
    if st == "mid": score["10"] += 1

    # Сон
    sl = data["sleep"]
    if sl == "bad": score["13"] += 2
    if sl == "mid": score["10"] += 1

    parent_id = max(score, key=score.get)
    name = next(p["name"] for p in products if p["id"] == parent_id)

    explanations = {
        "1": "Помогает гормональному балансу, коже и метаболизму благодаря высокому уровню Омега-3.",
        "4": "Поддерживает пищеварение, печень и мягко снижает воспаление.",
        "7": "Сильно улучшает фокус, память и нервную систему.",
        "10": "Баланс Ω-3/6 снижает тревожность и стабилизирует настроение.",
        "13": "Мощный иммуномодулятор для восстановления после стресса и воспалений.",
        "16": "Отлично для кожи, энергии и мягкой поддержки ЖКТ.",
        "19": "Мягкое повседневное масло, подходит почти всем.",
    }

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Выбрать объём", callback_data=f"prod:{parent_id}")
    kb.button(text="💬 Консультация", callback_data=f"chat:start:{parent_id}")
    kb.adjust(1)

    await cb.message.edit_text(
        f"🌿 <b>Ваше персональное масло</b>\n\n"
        f"<b>{name}</b>\n{explanations[parent_id]}\n\n"
        f"⬇ Что хотите сделать дальше?",
        reply_markup=kb.as_markup()
    )


# ===============================================================
# AI CHAT
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("chat:start:"))
async def chat_start(cb, state):
    pid = cb.data.split(":")[2]
    await state.set_state(OilWizard.chat)
    await state.update_data(pid=pid)

    await cb.message.edit_text(
        "💬 <b>Задайте вопрос</b>\n"
        "Можете спросить о применении, дозировке, противопоказаниях или сочетании масел."
    )


@oil_router.message(OilWizard.chat)
async def chat_ai(msg, state):
    data = await state.get_data()
    pid = data["pid"]

    NAME_MAP = {
        "1": "Льняное масло",
        "4": "Тыквенное масло",
        "7": "Масло грецкого ореха",
        "10": "Масло конопляное",
        "13": "Масло чёрного тмина",
        "16": "Масло кокосовое",
        "19": "Масло подсолнечное",
    }

    name = NAME_MAP.get(pid, "Масло")

    answer = (
        f"🧬 <b>{name}</b>\n\n"
        "Рекомендации по применению:\n"
        "• Принимать по 1 ч.л. утром натощак 30 дней.\n"
        "• Можно добавлять в салаты.\n"
        "• Не жарить — Омега-жиры разрушаются.\n"
        "• При чувствительном ЖКТ — начинать с 1/2 ч.л. и увеличивать постепенно.\n\n"
        "Задавайте дальнейшие вопросы 😊"
    )

    await msg.answer(answer)
