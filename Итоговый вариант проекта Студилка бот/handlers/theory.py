# handlers/theory.py

from aiogram import types
from aiogram.fsm.context import FSMContext
from config.bot_config import dp, bot
from states.user_states import UserState
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import logging


GROUP_CHAT_ID = "@studilka_community"
GROUP_LINK = "https://t.me/+ef4JOpZGsfU5OWIy"
YANDEX_DISK_LINK = "https://disk.yandex.ru/d/otukMheq-nALkQ"


async def check_group_membership(user_id: int) -> bool:
    """Проверка подписки на группу"""
    try:
        try:
            chat = await bot.get_chat(GROUP_CHAT_ID)
            chat_id = chat.id
            logging.info(f"Found chat ID: {chat_id}")
        except Exception as e:
            logging.error(f"Error getting chat: {e}")
            chat = await bot.get_chat("@studilka_community")
            chat_id = chat.id
            logging.info(f"Found chat ID through second link: {chat_id}")

        # Проверяем членство
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
        logging.info(f"Checking membership for user {user_id}: {is_member} (status: {member.status})")
        return is_member
    except Exception as e:
        logging.error(f"Error checking group membership for user {user_id}: {e}")
        return False


@dp.callback_query(lambda c: c.data == "theory")
async def process_theory(callback: types.CallbackQuery):
    try:
        await callback.answer()

        message_text = f"""📚 Для доступа к теории необходимо:

1️⃣ Вступить в нашу группу: [Ссылка на группу]({GROUP_LINK})

После выполнения условия нажмите кнопку "Проверить доступ" ⬇️"""

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Проверить доступ", callback_data="check_theory_access")
        builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
        builder.adjust(1)

        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise e


@dp.callback_query(lambda c: c.data == "check_theory_access")
async def check_theory_access(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        user_id = callback.from_user.id

        logging.info(f"Checking access for user {user_id}")

        # Проверяем подписку
        is_member = await check_group_membership(user_id)
        logging.info(f"Membership check result for user {user_id}: {is_member}")

        if not is_member:
            message_text = f"""❌ Вы еще не подписались на группу!

📢 Для доступа к теории необходимо:
1️⃣ Вступить в нашу группу: [Ссылка на группу]({GROUP_LINK})

Пожалуйста, подпишитесь и нажмите кнопку "Проверить доступ" снова."""

            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Проверить доступ", callback_data="check_theory_access")
            builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
            builder.adjust(1)

        else:
            message_text = f"""✅ Поздравляем! 

📚 Вот ссылка на теоретические материалы: [Яндекс.Диск]({YANDEX_DISK_LINK})

⚠️ Пожалуйста, не делитесь этой ссылкой с другими пользователями."""

            await state.set_state(UserState.selecting_subject)
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
            builder.adjust(1)

        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise e
