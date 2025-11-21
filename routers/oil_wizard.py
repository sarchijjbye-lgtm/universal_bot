# routers/oil_wizard.py

from aiogram import Router, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

oil_router = Router()


# ===============================================================
# FSM — состояния
# ===============================================================
class OilWizard(StatesGroup):
    goals = State()
    lifestyle = State()
    allergies = State()
    activity = State()
    age = State()
    sex = State()
    adaptive = State()
    result = State()
    chat = State()  # мини-чат AI после результата


# ===============================================================
# Мультиселект клавиатура
# ===============================================================
def multiselect(options: dict, selected: set, with_back=False, back_cb="back"):
    kb = InlineKeyboardBuilder()

    for key, label in options.items():
        prefix = "🟩 " if key in selected else "⬜ "
        kb.button(text=prefix + label, callback_data=f"ms:{key}")

    if with_back:
        kb.button(text="⬅️ Назад", callback_data=back_cb)

    kb.button(text="➡️ Готово", callback_data="ms:done")
    kb.adjust(1)
    return kb.as_markup()


# ===============================================================
# Кнопка «Назад» — отдельный бейк
# ===============================================================
def back_btn(cb):
    # Для удобства
    return InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data=cb).adjust(1).as_markup()


# ===============================================================
# Старт
# ===============================================================
@oil_router.message(lambda m: m.text in ["🧬 Подбор масла", "🧬 Идеальный подбор масла"])
async def start_quiz(msg: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OilWizard.goals)
    await state.update_data(goals=set())

    await msg.answer(
        "🧬 <b>Подбор масла</b>\n\n"
        "Отвечай на вопросы — я подберу масло как нутрициолог.\nВыбирай несколько вариантов:",
        reply_markup=multiselect({
            "energy": "Энергия",
            "brain": "Память / Фокус",
            "immunity": "Иммунитет",
            "digestion": "Пищеварение",
            "skin": "Кожа и волосы",
            "stress": "Стресс и сон",
            "weight": "Метаболизм / Вес",
            "male": "Мужское здоровье",
            "female": "Женское здоровье",
        }, set())
    )


# ===============================================================
# GOALS
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.text.startswith("🧬"))
async def q_goals(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data["goals"])

    key = cb.data.split(":")[1]

    if key == "done":
        if not selected:
            return await cb.answer("Выберите хотя бы одну цель", show_alert=True)

        await state.set_state(OilWizard.lifestyle)
        await state.update_data(lifestyle=set())

        await cb.message.edit_text(
            "🥗 <b>Как питаешься?</b>",
            reply_markup=multiselect({
                "fat": "Много жирного",
                "sweet": "Сладкое",
                "fish_low": "Мало рыбы",
                "veg_low": "Мало овощей",
                "normal": "Обычное питание",
                "sport": "Спорт",
            }, set(), with_back=True, back_cb="back:goals")
        )
        return

    # toggle
    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(goals=selected)
    await cb.message.edit_reply_markup(multiselect({
        "energy": "Энергия",
        "brain": "Память / Фокус",
        "immunity": "Иммунитет",
        "digestion": "Пищеварение",
        "skin": "Кожа и волосы",
        "stress": "Стресс и сон",
        "weight": "Метаболизм / Вес",
        "male": "Мужское здоровье",
        "female": "Женское здоровье",
    }, selected))


# ===============================================================
# BACK: from LIFESTYLE → GOALS
# ===============================================================
@oil_router.callback_query(lambda c: c.data == "back:goals")
async def back_to_goals(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sel = data["goals"]

    await state.set_state(OilWizard.goals)
    await cb.message.edit_text(
        "🧬 <b>Подбор масла</b>",
        reply_markup=multiselect({
            "energy": "Энергия",
            "brain": "Память / Фокус",
            "immunity": "Иммунитет",
            "digestion": "Пищеварение",
            "skin": "Кожа и волосы",
            "stress": "Стресс и сон",
            "weight": "Метаболизм / Вес",
            "male": "Мужское здоровье",
            "female": "Женское здоровье",
        }, sel)
    )


# ===============================================================
# LIFESTYLE
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.text.startswith("🥗"))
async def q_lifestyle(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data["lifestyle"])
    key = cb.data.split(":")[1]

    if key == "done":
        await state.set_state(OilWizard.allergies)
        await state.update_data(allergies=set())

        await cb.message.edit_text(
            "😌 <b>Есть аллергии или особенности?</b>",
            reply_markup=multiselect({
                "nuts": "Аллергия на орехи",
                "seeds": "На семена",
                "sensitive": "Чувствительный ЖКТ",
                "none": "Нет",
            }, set(), with_back=True, back_cb="back:lifestyle")
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
        "sport": "Спорт",
    }, selected, with_back=True, back_cb="back:goals"))


# ===============================================================
# BACK lifestyle → goals
# ===============================================================
@oil_router.callback_query(lambda c: c.data == "back:lifestyle")
async def back_to_lifestyle(cb, state):
    data = await state.get_data()
    sel = data["lifestyle"]

    await state.set_state(OilWizard.lifestyle)
    await cb.message.edit_text(
        "🥗 <b>Как питаешься?</b>",
        reply_markup=multiselect({
            "fat": "Много жирного",
            "sweet": "Сладкое",
            "fish_low": "Мало рыбы",
            "veg_low": "Мало овощей",
            "normal": "Обычное питание",
            "sport": "Спорт",
        }, sel, with_back=True, back_cb="back:goals")
    )


# ===============================================================
# ALLERGIES
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("ms:") and c.message.text.startswith("😌"))
async def q_allergies(cb, state):
    data = await state.get_data()
    selected = set(data["allergies"])
    key = cb.data.split(":")[1]

    if key == "done":
        await state.set_state(OilWizard.activity)

        kb = InlineKeyboardBuilder()
        kb.button(text="Низкая", callback_data="act:low")
        kb.button(text="Средняя", callback_data="act:mid")
        kb.button(text="Высокая", callback_data="act:high")
        kb.button(text="⬅️ Назад", callback_data="back:allergies")
        kb.adjust(1)

        await cb.message.edit_text("⚡ <b>Уровень активности:</b>", reply_markup=kb.as_markup())
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.add(key)

    await state.update_data(allergies=selected)

    await cb.message.edit_reply_markup(multiselect({
        "nuts": "Аллергия на орехи",
        "seeds": "На семена",
        "sensitive": "Чувствительный ЖКТ",
        "none": "Нет",
    }, selected, with_back=True, back_cb="back:lifestyle"))


@oil_router.callback_query(lambda c: c.data == "back:allergies")
async def back_to_allergies(cb, state):
    data = await state.get_data()
    sel = data["allergies"]
    await state.set_state(OilWizard.allergies)

    await cb.message.edit_text(
        "😌 <b>Есть аллергии или особенности?</b>",
        reply_markup=multiselect({
            "nuts": "Аллергия на орехи",
            "seeds": "На семена",
            "sensitive": "Чувствительный ЖКТ",
            "none": "Нет",
        }, sel, with_back=True, back_cb="back:lifestyle")
    )


# ===============================================================
# ACTIVITY
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("act:"))
async def q_activity(cb, state):
    await state.update_data(activity=cb.data.split(":")[1])
    await state.set_state(OilWizard.age)

    kb = InlineKeyboardBuilder()
    kb.button(text="16–25", callback_data="age:16")
    kb.button(text="26–40", callback_data="age:26")
    kb.button(text="40–55", callback_data="age:40")
    kb.button(text="55+", callback_data="age:55")
    kb.button(text="⬅️ Назад", callback_data="back:activity")
    kb.adjust(1)

    await cb.message.edit_text("🎯 <b>Возраст:</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back:activity")
async def back_to_activity(cb, state):
    await state.set_state(OilWizard.activity)

    kb = InlineKeyboardBuilder()
    kb.button(text="Низкая", callback_data="act:low")
    kb.button(text="Средняя", callback_data="act:mid")
    kb.button(text="Высокая", callback_data="act:high")
    kb.button(text="⬅️ Назад", callback_data="back:allergies")
    kb.adjust(1)

    await cb.message.edit_text("⚡ <b>Уровень активности:</b>", reply_markup=kb.as_markup())


# ===============================================================
# AGE → SEX
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("age:"))
async def q_age(cb, state):
    await state.update_data(age=cb.data.split(":")[1])
    await state.set_state(OilWizard.sex)

    kb = InlineKeyboardBuilder()
    kb.button(text="Мужской", callback_data="sex:m")
    kb.button(text="Женский", callback_data="sex:f")
    kb.button(text="⬅️ Назад", callback_data="back:age")
    kb.adjust(1)

    await cb.message.edit_text("🧬 <b>Пол:</b>", reply_markup=kb.as_markup())


@oil_router.callback_query(lambda c: c.data == "back:age")
async def back_to_age(cb, state):
    await state.set_state(OilWizard.age)

    kb = InlineKeyboardBuilder()
    kb.button(text="16–25", callback_data="age:16")
    kb.button(text="26–40", callback_data="age:26")
    kb.button(text="40–55", callback_data="age:40")
    kb.button(text="55+", callback_data="age:55")
    kb.button(text="⬅️ Назад", callback_data="back:activity")
    kb.adjust(1)

    await cb.message.edit_text("🎯 <b>Возраст:</b>", reply_markup=kb.as_markup())


# ===============================================================
# SEX → adaptive or finish
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("sex:"))
async def q_sex(cb, state):
    await state.update_data(sex=cb.data.split(":")[1])
    data = await state.get_data()

    goals = data["goals"]

    if "brain" in goals:
        await state.set_state(OilWizard.adaptive)

        kb = InlineKeyboardBuilder()
        kb.button(text="Часто", callback_data="extra:high")
        kb.button(text="Иногда", callback_data="extra:mid")
        kb.button(text="Редко", callback_data="extra:low")
        kb.button(text="⬅️ Назад", callback_data="back:sex")
        kb.adjust(1)

        await cb.message.edit_text("🧠 <b>Чувствуешь умственную усталость?</b>", reply_markup=kb.as_markup())
        return

    if "digestion" in goals:
        await state.set_state(OilWizard.adaptive)

        kb = InlineKeyboardBuilder()
        kb.button(text="Да", callback_data="extra:yes")
        kb.button(text="Иногда", callback_data="extra:mid")
        kb.button(text="Нет", callback_data="extra:no")
        kb.button(text="⬅️ Назад", callback_data="back:sex")
        kb.adjust(1)

        await cb.message.edit_text("🍏 <b>Бывает вздутие?</b>", reply_markup=kb.as_markup())
        return

    # иначе сразу результат
    await finish_recommendation(cb, state)


@oil_router.callback_query(lambda c: c.data == "back:sex")
async def back_to_sex(cb, state):
    await state.set_state(OilWizard.sex)

    kb = InlineKeyboardBuilder()
    kb.button(text="Мужской", callback_data="sex:m")
    kb.button(text="Женский", callback_data="sex:f")
    kb.button(text="⬅️ Назад", callback_data="back:age")
    kb.adjust(1)

    await cb.message.edit_text("🧬 <b>Пол:</b>", reply_markup=kb.as_markup())


# ===============================================================
# ADAPTIVE
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("extra:"))
async def q_adaptive(cb, state):
    await state.update_data(extra=cb.data.split(":")[1])
    await finish_recommendation(cb, state)


# ===============================================================
# FINISH — ENGINE
# ===============================================================
async def finish_recommendation(cb, state):
    data = await state.get_data()
    await state.clear()

    products = load_products_safe()

    score = {
        "1": 0,  # льняное
        "4": 0,  # тыквенное
        "7": 0,  # грецкое
    }

    # логика
    if "energy" in data["goals"]:
        score["7"] += 2
    if "brain" in data["goals"]:
        score["7"] += 3
        score["1"] += 1
    if "immunity" in data["goals"]:
        score["4"] += 2
    if "digestion" in data["goals"]:
        score["4"] += 3
    if "skin" in data["goals"]:
        score["1"] += 2
    if "stress" in data["goals"]:
        score["7"] += 2
    if "weight" in data["goals"]:
        score["1"] += 3
    if "male" in data["goals"]:
        score["4"] += 3

    # аллергии
    if "nuts" in data["allergies"]:
        score["7"] -= 999
    if "seeds" in data["allergies"]:
        score["1"] -= 999
        score["4"] -= 999

    # adaptive
    if data.get("extra") == "high":
        score["7"] += 2
    if data.get("extra") == "yes":
        score["4"] += 2

    best = max(score, key=score.get)
    parent_id = best

    name = next(p["name"] for p in products if p["id"] == parent_id)

    explanations = {
        "1": "Идеально для обмена веществ, кожи и гормонального баланса.",
        "4": "Лучшее для печени, иммунитета и мужского здоровья.",
        "7": "Оптимально для мозга, энергии, концентрации и нервной системы.",
    }

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Выбрать объём", callback_data=f"prod:{parent_id}")
    kb.button(text="💬 Задать вопрос", callback_data=f"chat:start:{parent_id}")
    kb.adjust(1)

    await cb.message.edit_text(
        f"🌿 <b>Твоя рекомендация</b>\n\n"
        f"<b>{name}</b>\n{explanations[parent_id]}\n\n"
        f"Что дальше?",
        reply_markup=kb.as_markup()
    )


# ===============================================================
# MINICHAT — AI CONSULTATION MODE
# ===============================================================
@oil_router.callback_query(lambda c: c.data.startswith("chat:start:"))
async def start_chat(cb, state):
    parent_id = cb.data.split(":")[2]
    await state.set_state(OilWizard.chat)
    await state.update_data(product_id=parent_id)

    await cb.message.edit_text(
        "💬 <b>Консультация</b>\n"
        "Задай вопрос о применении, противопоказаниях или схемах приёма.\n\n"
        "Напиши сообщение ниже:"
    )


@oil_router.message(OilWizard.chat)
async def chat_ai(msg, state):
    data = await state.get_data()
    product_id = data["product_id"]

    # Простая экспертная модель
    NAME_MAP = {
        "1": "Льняное масло",
        "4": "Тыквенное масло",
        "7": "Масло грецкого ореха",
    }

    answer = (
        f"🧬 <b>{NAME_MAP[product_id]}</b>\n\n"
        "Вот мой совет:\n\n"
        "• Принимать по 1 ч.л. утром натощак.\n"
        "• Курс 30 дней.\n"
        "• Можно добавлять в салаты.\n"
        "• Не жарить — теряются Омега-жиры.\n\n"
        "Если хочешь схему под твои цели — уточни вопрос 😉"
    )

    await msg.answer(answer)
