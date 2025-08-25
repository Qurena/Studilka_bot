# keyboards/base_menu_buttons.py

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config.data_config import SUBJECTS


def get_base_menu_keyboard() -> ReplyKeyboardMarkup:
    """Создает базовую клавиатуру с основными кнопками меню"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📚 Тесты")
    builder.button(text="👤 Личный кабинет")
    builder.button(text="📖 Теория")
    builder.button(text="📚 Учебники")
    builder.button(text="ℹ️ Помощь")
    
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


async def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='ЕГЭ тесты', callback_data='ege_tests')
    builder.button(text='Личный кабинет', callback_data='personal_account')
    builder.button(text='Теория', callback_data='theory')
    builder.button(text='Учебники', callback_data='textbooks')
    builder.button(text='Факты', callback_data='facts')
    builder.adjust(1)
    return builder.as_markup()


async def get_subjects_keyboard(callback_prefix="subject") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject_name, subject_code in SUBJECTS.items():
        builder.button(text=subject_name, callback_data=f"{callback_prefix}_{subject_code}")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


async def get_classes_keyboard(back_callback) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for class_num in ["10", "11"]:
        builder.button(text=f"{class_num} класс", callback_data=f"class_{class_num}")
    builder.button(text="⬅️ Назад", callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()


async def get_personal_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика тестов", callback_data="user_stats")
    builder.button(text="🎯 Мои цели", callback_data="user_goals")
    builder.button(text="📝 История занятий", callback_data="user_history")
    builder.button(text="🏆 Результаты", callback_data="user_results_menu")
    builder.button(text="🗑️ Стереть статистику", callback_data="clear_user_stats")
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()
