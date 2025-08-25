# handlers/personal.py

from aiogram.exceptions import TelegramBadRequest

from database import get_user_activity
from keyboards.base_menu_buttons import get_base_menu_keyboard
from keyboards.base_menu_buttons import get_personal_keyboard
from .purpose import *
from .tests import end_test

# Логирование
logging.basicConfig(level=logging.INFO)


@dp.callback_query(lambda c: c.data == "personal_account")
async def process_personal_account(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id

        # Получаем данные из бд
        test_results = user_data_manager.get_user_results(user_id)
        profile = user_data_manager.get_profile(user_id)

        total_tests = len(test_results)
        total_score = sum(result['score'] for result in test_results)
        max_possible = sum(result['max_score'] for result in test_results)

        message_text = f"""📊 Личный кабинет

🏆 Баллы: {total_score}/{max_possible if max_possible > 0 else 'N/A'}
📝 Пройдено тестов: {total_tests}
🆔 Ваш ID: {user_id}

Статистика ведется по любым прохождениям тестов"""

        keyboard = await get_personal_keyboard()

        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Ошибка в process_personal_account: {e}")
        await callback.message.answer(f"Произошла ошибка при загрузке личного кабинета: {str(e)}")


@dp.callback_query(lambda c: c.data == "user_stats")
async def process_user_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    test_results = user_data_manager.get_user_results(user_id)

    total_correct = sum(result['score'] for result in test_results)
    total_questions = sum(result['max_score'] for result in test_results)

    subject_results = {}
    for result in test_results:
        subject = 'rus' if 'rus' in result['test_id'] else 'math'

        if subject not in subject_results:
            subject_results[subject] = {
                'total_score': 0,
                'max_score': 0,
                'attempts': 0
            }

        subject_results[subject]['total_score'] += result['score']
        subject_results[subject]['max_score'] += result['max_score']
        subject_results[subject]['attempts'] += 1

    # Вычисляем средний балл и колво неправильных ответов
    avg_score = total_correct / total_questions * 100 if total_questions > 0 else 0
    wrong_answers = total_questions - total_correct if total_questions > 0 else 0

    subject_names = {
        'rus': 'Русский язык',
        'math': 'Математика'
    }

    stats_text = f"""📊 <b>Статистика тестов</b>

📈 Процент правильных ответов: {avg_score:.1f}%
✅ Правильных ответов: {total_correct}
❌ Неправильных ответов: {wrong_answers}
📝 Всего попыток: {len(test_results)}

🎯 Результаты по предметам:"""

    for subj, data in subject_results.items():
        if data['max_score'] > 0:
            percent = data['total_score'] / data['max_score'] * 100
            stats_text += f"\n• {subject_names.get(subj, subj)}: {data['total_score']} из {data['max_score']} ({percent:.1f}%)"

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в профиль", callback_data="personal_account")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        stats_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"Статистика тестов для пользователя {user_id} обновлена.")


@dp.callback_query(lambda c: c.data == "user_results_menu")
async def user_results_menu(callback: types.CallbackQuery):
    await callback.answer()

    results_menu_text = "Выберите предмет для просмотра результатов:"
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Русский язык", callback_data="user_results_rus")
    builder.button(text="📚 Математика", callback_data="user_results_math")
    builder.button(text="⬅️ Назад", callback_data="personal_account")
    builder.adjust(1)

    await callback.message.edit_text(
        results_menu_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"Пользователь {callback.from_user.id} открыл меню результатов.")


def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад к выбору предмета", callback_data="user_results_menu")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(lambda c: c.data.startswith("user_results_") and len(c.data.split("_")) == 3)
async def process_user_results(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    logging.info(f"Retrieving results for user_id: {user_id}")
    subject = callback.data.split("_")[2]

    # Получаем данные из бд
    all_results = user_data_manager.get_user_results(user_id)

    subject_results = [result for result in all_results if subject in result['test_id']]
    logging.info(f"Found {len(subject_results)} results for subject {subject}")

    if not subject_results:
        await callback.message.edit_text(
            "❌ Нет данных о результатах.\nПройдите тест, чтобы увидеть свои результаты!",
            reply_markup=get_back_keyboard()
        )
        return

    # Группируем результаты по годам
    years = {}
    for result in subject_results:
        year = next((y for y in ["2025", "2024"] if y in result['test_id']), "Другой")

        if year not in years:
            years[year] = []

        years[year].append(result)

    results_text = f"🏆 Результаты тестов по {subject.upper()}:\n\n"

    for year, year_results in sorted(years.items(), reverse=True):
        if year_results:
            best_score = max(r['score'] for r in year_results)
            max_possible = year_results[0]['max_score']  # Предполагаем, что все тесты одного года имеют одинаковое max_score
            all_scores = [r['score'] for r in year_results]

            results_text += f"🎯 Демоверсия {year}:\n"
            results_text += f"• Лучший результат: {best_score} из {max_possible} баллов\n"
            results_text += f"• История попыток: {', '.join(map(str, all_scores))}\n\n"

    if subject_results:
        avg_score = sum(r['score'] for r in subject_results) / len(subject_results)
        total_attempts = len(subject_results)

        results_text += f"\n📊 Общая статистика:\n"
        results_text += f"• Среднее количество баллов: {avg_score:.1f}\n"
        results_text += f"• Всего попыток: {total_attempts}"

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад к выбору предмета", callback_data="user_results_menu")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        results_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(lambda c: c.data == "finish_test")
async def finish_test_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await end_test(callback.message, state, is_early_end=False)
    except Exception as e:
        logging.error(f"Error in finish_test_handler: {e}")


def format_time_hms(seconds: float) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours} ч {minutes} мин {secs} сек"
    elif minutes > 0:
        return f"{minutes} мин {secs} сек"
    else:
        return f"{secs} сек"


@dp.callback_query(lambda c: c.data == "user_history")
async def process_user_history(callback: types.CallbackQuery):
    global datetime
    await callback.answer()
    user_id = callback.from_user.id

    # Получаем данные из бд
    test_results = user_data_manager.get_user_results(user_id)
    lesson_history = user_data_manager.get_lesson_history(user_id)

    activity = get_user_activity(user_id)
    first_seen = activity.get('first_seen')
    if first_seen:
        from datetime import datetime
        first_seen_dt = datetime.fromisoformat(first_seen)
        now = datetime.now()
        total_seconds = (now - first_seen_dt).total_seconds()
        total_time_str = format_time_hms(total_seconds)
    else:
        total_time_str = "нет данных"

    sorted_results = sorted(test_results, key=lambda x: x['timestamp'], reverse=True)

    last_sessions = []

    subject_names = {
        'rus': 'Русский язык',
        'math': 'Математика'
    }

    for result in sorted_results[:3]:
        test_id = result['test_id']
        subject = next((name for key, name in subject_names.items() if key in test_id), 'Другое')
        score = f"{result['score']}/{result['max_score']}"
        completion_time = result['timestamp']

        session_str = f"• {subject} - {score} - {completion_time}"
        last_sessions.append(session_str)

    while len(last_sessions) < 3:
        last_sessions.append("• Нет данных")

    current_time = datetime.now().strftime("%H:%M:%S")

    history_text = f"""📝 <b>История занятий</b>\n🔄 Обновлено в {current_time}\n\n⏱ Общее время в боте: {total_time_str}\n\n🕒 Последние занятия:\n{last_sessions[0]}\n{last_sessions[1]}\n{last_sessions[2]}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="refresh_history")
    builder.button(text="⬅️ Назад в профиль", callback_data="personal_account")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        history_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    logging.info(f"История занятий для пользователя {user_id} обновлена.")


# Обновляем историю попыток
@dp.callback_query(lambda c: c.data == "refresh_history")
async def refresh_history(callback: types.CallbackQuery):
    await callback.answer("🔄 Обновлено!")
    user_id = callback.from_user.id

    # Получаем данные из бд
    test_results = user_data_manager.get_user_results(user_id)
    lesson_history = user_data_manager.get_lesson_history(user_id)
    activity = get_user_activity(user_id)
    first_seen = activity.get('first_seen')
    if first_seen:
        from datetime import datetime
        first_seen_dt = datetime.fromisoformat(first_seen)
        now = datetime.now()
        total_seconds = (now - first_seen_dt).total_seconds()
        total_time_str = format_time_hms(total_seconds)
    else:
        total_time_str = "нет данных"

    sorted_results = sorted(test_results, key=lambda x: x['timestamp'], reverse=True)

    last_sessions = []

    subject_names = {
        'rus': 'Русский язык',
        'math': 'Математика'
    }

    # Добавляем последние тесты
    for result in sorted_results[:3]:
        test_id = result['test_id']
        subject = next((name for key, name in subject_names.items() if key in test_id), 'Другое')
        score = f"{result['score']}/{result['max_score']}"
        completion_time = result['timestamp']

        session_str = f"• {subject} - {score} - {completion_time}"
        last_sessions.append(session_str)

    while len(last_sessions) < 3:
        last_sessions.append("• Нет данных")

    current_time = datetime.now().strftime("%H:%M:%S")

    history_text = f"""📝 <b>История занятий</b>\n🔄 Обновлено в {current_time}\n\n⏱ Общее время в боте: {total_time_str}\n\n🕒 Последние занятия:\n{last_sessions[0]}\n{last_sessions[1]}\n{last_sessions[2]}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="refresh_history")
    builder.button(text="⬅️ Назад в профиль", callback_data="personal_account")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    try:
        await callback.message.edit_text(
            history_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        logging.info(f"История занятий для пользователя {user_id} обновлена.")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные уже актуальны!")
            logging.info(f"Данные для пользователя {user_id} уже актуальны.")
        else:
            raise


@dp.message(lambda message: message.text == "👤 Личный кабинет")
async def personal_cabinet(message: types.Message):
    """Обработчик кнопки личного кабинета"""
    try:
        user_id = message.from_user.id

        # Получаем профиль пользователя
        profile = user_data_manager.get_profile(user_id)
        if not profile:
            profile = {}

        test_results = user_data_manager.get_user_results(user_id)
        total_tests = len(test_results)

        total_score = 0
        total_questions = 0
        subject_stats = {'rus': {'total': 0, 'correct': 0}, 'math': {'total': 0, 'correct': 0}}

        for result in test_results:
            total_score += result['score']
            total_questions += result['max_score']

            subject = 'rus' if 'rus' in result['test_id'] else 'math'
            subject_stats[subject]['total'] += result['max_score']
            subject_stats[subject]['correct'] += result['score']

        avg_score = (total_score / total_questions * 100) if total_questions > 0 else 0

        message_text = (
            "👤 *Личный кабинет*\n\n"
            f"📊 *Общая статистика:*\n"
            f"• Всего тестов: {total_tests}\n"
            f"• Общий результат: {total_score}/{total_questions}\n"
            f"• Средний процент: {avg_score:.1f}%\n\n"
        )

        message_text += "*Статистика по предметам:*\n"
        for subject, stats in subject_stats.items():
            if stats['total'] > 0:
                subject_name = "Русский язык" if subject == 'rus' else "Математика"
                subject_percent = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                message_text += f"• {subject_name}: {stats['correct']}/{stats['total']} ({subject_percent:.1f}%)\n"

        message_text += "\n"

        if profile.get('full_name'):
            message_text += f"👤 *Имя:* {profile['full_name']}\n"
        if profile.get('education_level'):
            message_text += f"🎓 *Уровень образования:* {profile['education_level']}\n"
        if profile.get('study_goals'):
            message_text += f"🎯 *Цели обучения:* {profile['study_goals']}\n"

        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Результаты тестов", callback_data="user_results_menu")
        builder.button(text="✏️ Редактировать профиль", callback_data="edit_profile")
        builder.button(text="📚 История занятий", callback_data="lesson_history")
        builder.adjust(1)

        await message.answer(
            text=message_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Ошибка при открытии личного кабинета: {e}")
        await message.answer(
            "Произошла ошибка при загрузке личного кабинета. Попробуйте позже.",
            reply_markup=get_base_menu_keyboard()
        )

@dp.callback_query(lambda c: c.data == "clear_user_stats")
async def clear_user_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        from database import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM user_profile WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM user_access WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM test_results WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM lesson_history WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM user_activity WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await callback.answer("Ваша статистика и профиль полностью очищены!", show_alert=True)
        from keyboards.base_menu_buttons import get_base_menu_keyboard
        await callback.message.edit_text(
            "Ваш профиль и статистика полностью очищены.\n\nВы в главном меню.",
            reply_markup=await get_personal_keyboard()
        )
        logging.info(f"Пользователь {user_id} полностью очистил свой профиль и статистику.")
    except Exception as e:
        logging.error(f"Ошибка при очистке профиля пользователя: {e}")
        await callback.answer("Произошла ошибка при очистке профиля.", show_alert=True)


@dp.callback_query(lambda c: c.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery):
    """Возврат в личный кабинет"""
    await personal_cabinet(callback.message)
