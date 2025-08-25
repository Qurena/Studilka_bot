#handlers/purpose.py

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import logging

from config.bot_config import dp
from data_storage import user_data_manager

# Логирование
logging.basicConfig(level=logging.INFO)

# формат: ДД.ММ.ГГГГ
EXAM_DATES = {
    'math': '27.05.2025',
    'rus': '30.05.2025'
}


# Склоняем слово "день"
def decline_days(number: int) -> str:
    if number % 100 in [11, 12, 13, 14]:
        return "дней"

    last_digit = number % 10
    if last_digit == 1:
        return "день"
    elif last_digit in [2, 3, 4]:
        return "дня"
    else:
        return "дней"


def calculate_days_until_exams() -> dict:
    """Рассчитывает количество дней до каждого экзамена"""
    today = datetime.now()
    days_until = {}

    for subject, date_str in EXAM_DATES.items():
        exam_date = datetime.strptime(date_str, "%d.%m.%Y")
        days_left = (exam_date - today).days
        days_left = max(0, days_left)
        days_until[subject] = {
            'days': days_left,
            'word': decline_days(days_left)
        }

    return days_until


@dp.callback_query(lambda c: c.data == "user_goals")
async def process_user_goals(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    profile = user_data_manager.get_profile(user_id)

    rus_goal_value = profile.get('rus_goal') if profile else None
    math_goal_value = profile.get('math_goal') if profile else None

    rus_goal = f"{rus_goal_value} баллов" if rus_goal_value not in (None, 0) else 'Не установлена'
    math_goal = f"{math_goal_value} баллов" if math_goal_value not in (None, 0) else 'Не установлена'

    days_until = calculate_days_until_exams()

    goals_text = f"""🎯 <b>Мои цели</b>

📚 Текущие цели:
• Русский язык: {rus_goal}
• Математика: {math_goal}

⏳ Время до ЕГЭ:
• Профильная математика - {days_until['math']['days']} {days_until['math']['word']}
• Русский язык - {days_until['rus']['days']} {days_until['rus']['word']}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Установить цель РУС", callback_data="set_goal_rus")
    builder.button(text="✏️ Установить цель МАТ", callback_data="set_goal_math")
    builder.button(text="⬅️ Назад в профиль", callback_data="personal_account")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        goals_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"Цели пользователя {user_id} обновлены.")


@dp.callback_query(lambda c: c.data.startswith("set_goal_"))
async def process_set_goal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    subject = callback.data.split("_")[2]

    subject_names = {
        "rus": "русскому языку",
        "math": "математике"
    }

    await state.update_data(setting_goal_for=subject)

    goal_text = f"""✏️ <b>Установка цели по {subject_names[subject]}</b>

Выберите желаемый балл на ЕГЭ:"""

    builder = InlineKeyboardBuilder()
    for score in [60, 70, 80, 90, 100]:
        builder.button(
            text=f"{score} баллов",
            callback_data=f"goal_score_{subject}_{score}"
        )
    builder.button(text="⬅️ Назад к целям", callback_data="user_goals")
    builder.adjust(1)

    await callback.message.edit_text(
        goal_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"Пользователь {callback.from_user.id} начал установку цели по {subject_names[subject]}.")


@dp.callback_query(lambda c: c.data.startswith("goal_score_"))
async def process_goal_score(callback: types.CallbackQuery):
    await callback.answer()
    _, _, subject, score = callback.data.split("_")
    user_id = callback.from_user.id

    # Сохраняем цель в бд
    profile_update = {f'{subject}_goal': int(score)}
    user_data_manager.update_profile(user_id, profile_update)

    subject_names = {
        "rus": "русскому языку",
        "math": "математике"
    }

    confirmation_text = f"""✅ <b>Цель установлена!</b>

🎯 Ваша цель по {subject_names[subject]}: {score} баллов

💪 Удачи в подготовке!"""

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад к целям", callback_data="user_goals")
    builder.button(text="⬅️ В личный кабинет", callback_data="personal_account")
    builder.adjust(1)

    await callback.message.edit_text(
        confirmation_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"Цель по {subject_names[subject]} установлена для пользователя {user_id}: {score} баллов.")
