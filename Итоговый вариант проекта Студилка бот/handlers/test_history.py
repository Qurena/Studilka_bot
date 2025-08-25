# handlers/test_history.py

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.bot_config import dp
from .tests import end_test
import logging

# Логирование
logging.basicConfig(level=logging.INFO)


@dp.callback_query(lambda c: c.data == "finish_test")
async def finish_test_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await end_test(callback.message, state, is_early_end=False)
    except Exception as e:
        logging.error(f"Error in finish_test_handler: {e}")


def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад к выбору предмета", callback_data="user_results_menu")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()
