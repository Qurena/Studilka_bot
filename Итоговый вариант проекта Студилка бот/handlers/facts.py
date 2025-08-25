#handlers/facts.py

import logging
import random

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.bot_config import dp

EGE_FACTS = [
    "🎓 Первый обязательный ЕГЭ в России прошел в 2009 году.",

    "📊 Каждый год ЕГЭ сдают более 750 000 выпускников по всей России.",

    "🌍 ЕГЭ признается в более чем 20 странах мира при поступлении в университеты.",

    "⏰ Самый длинный экзамен ЕГЭ - математика профильного уровня (235 минут).",

    "📝 На ЕГЭ по русскому языку участники пишут сочинение объемом не менее 150 слов.",

    "💻 С 2021 года ЕГЭ по информатике проводится в компьютерной форме.",

    "🔍 Все бланки ЕГЭ сканируются и проверяются в специальных центрах обработки информации.",

    "📱 На ЕГЭ запрещено иметь при себе средства связи, но разрешены простые часы.",

    "🎯 100 баллов по ЕГЭ ежегодно получают менее 1% участников.",

    "🌟 Результаты ЕГЭ действительны в течение 4 лет после сдачи экзамена."
]


@dp.callback_query(lambda c: c.data == "facts")
async def process_facts(callback: types.CallbackQuery):

    await callback.answer()

    fact = random.choice(EGE_FACTS)

    facts_text = f"""<b>Интересный факт о ЕГЭ:</b>

{fact}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Следующий факт", callback_data="facts")
    builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
    builder.adjust(1)

    try:
        await callback.message.edit_text(
            facts_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        logging.info(f"Показан факт пользователю {callback.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при показе факта: {e}")