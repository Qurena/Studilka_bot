#handlers/menu.py

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from aiogram import types
from aiogram.filters.command import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import bold

from config.bot_config import dp
from config.test_config import TESTS_BY_YEAR


logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "bot_db.sqlite"

os.makedirs(DB_DIR, exist_ok=True)


async def track_user_time(user_id: int):
    """Обновление времени последней активности"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER PRIMARY KEY,
            last_activity TIMESTAMP
        )
        """)

        current_time = datetime.now().isoformat()
        cur.execute("""
        INSERT OR REPLACE INTO user_activity (user_id, last_activity)
        VALUES (?, ?)
        """, (user_id, current_time))

        conn.commit()
        conn.close()

    except Exception as e:
        logging.error(f"Ошибка при обновлении времени активности: {e}")
        logging.error(f"Путь к базе данных: {DB_PATH}")
        logging.error(f"Директория существует: {os.path.exists(DB_DIR)}")
        logging.error(f"Права доступа к директории: {oct(os.stat(DB_DIR).st_mode)[-3:]}")


@dp.message(CommandStart())
async def show_main_menu(message: types.Message):

    try:
        await track_user_time(message.from_user.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="📚 Учебники", callback_data="textbooks")
        builder.button(text="📝 Тесты ЕГЭ", callback_data="ege_tests")
        builder.adjust(1)

        await message.answer(
            "👋 Добро пожаловать! Выберите раздел:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logging.error(f"Ошибка при показе главного меню: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


@dp.callback_query(lambda c: c.data == "ege_tests")
async def show_subjects(callback: types.CallbackQuery):
    await callback.answer()
    await track_user_time(callback.from_user.id)

    message_text = "📚 Выберите предмет для тестирования:"

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Русский язык", callback_data="subject_rus")
    builder.button(text="📐 Математика", callback_data="subject_math")
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_main")
    builder.adjust(1)

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("subject_"))
async def process_subject_selection(callback: types.CallbackQuery):
    await callback.answer()
    subject = callback.data.split("_")[1]

    subject_name = TESTS_BY_YEAR[subject]["name"]
    message_text = f"📚 Выберите год для предмета {bold(subject_name)}:"

    builder = InlineKeyboardBuilder()
    for year in ["2025", "2024"]:
        builder.button(
            text=f"📅 {year}",
            callback_data=f"year_{subject}_{year}"
        )

    builder.button(text="⬅️ Назад к предметам", callback_data="ege_tests")
    builder.adjust(1)

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(lambda c: c.data.startswith("year_"))
async def process_year_selection(callback: types.CallbackQuery):
    await callback.answer()
    _, subject, year = callback.data.split("_")

    subject_name = TESTS_BY_YEAR[subject]["name"]

    message_text = f"""📚 {bold(subject_name)} - {year} год

Доступные варианты:"""

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📝 Вариант 1",
        callback_data=f"variant_{subject}_{year}_1"
    )

    builder.button(text="⬅️ Назад к годам", callback_data=f"subject_{subject}")
    builder.button(text="⬅️ К предметам", callback_data="ege_tests")
    builder.adjust(1)

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith("variant_"))
async def select_variant(callback: types.CallbackQuery):
    try:
        await callback.answer()
        _, subject, year, variant_num = callback.data.split("_")

        variant = "Вариант" if subject == "rus" else "Демоверсия" if year == "2025" else "Вариант"

        text = f"""📝 Выберите режим тестирования

📚 Предмет: {bold(TESTS_BY_YEAR[subject]["name"])}
📅 Год: {bold(year)}
📋 {bold(variant)}"""

        builder = InlineKeyboardBuilder()
        builder.button(text="▶️ Начать тест", callback_data=f"start_test_{subject}_{year}_{variant_num}")
        builder.button(text="⬅️ Назад к вариантам", callback_data=f"year_{subject}_{year}")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error in select_variant: {e}")


@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):

    await callback.answer()
    await track_user_time(callback.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Учебники", callback_data="textbooks")
    builder.button(text="📝 Тесты ЕГЭ", callback_data="ege_tests")
    builder.adjust(1)

    await callback.message.edit_text(
        "Выберите раздел:",
        reply_markup=builder.as_markup()
    )


@dp.message()
async def update_activity_message(message: types.Message):

    try:
        await track_user_time(message.from_user.id)
        logging.info(f"Активность обновлена для пользователя {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при обновлении активности: {e}")
