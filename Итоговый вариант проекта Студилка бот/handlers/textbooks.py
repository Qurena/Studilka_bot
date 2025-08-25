# handlers/textbooks.py

import logging

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.bot_config import dp, bot
from handlers.theory import check_group_membership


logging.basicConfig(level=logging.INFO)


GROUP_CHAT_ID = "@studilka_community"
CHANNEL_ID = "@watchyourheaad"
GROUP_LINK = "https://t.me/+ef4JOpZGsfU5OWIy"
YANDEX_DISK_LINK = "https://disk.yandex.ru/d/2Kz3UixNc3LlGA"


async def check_channel_membership(user_id: int) -> bool:
    """Проверка подписки на канал"""
    try:
        try:
            chat = await bot.get_chat(CHANNEL_ID)
            chat_id = chat.id
            logging.info(f"Found channel chat ID: {chat_id}")
        except Exception as e:
            logging.error(f"Error getting channel chat: {e}")
            return False

        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
        logging.info(f"Checking channel membership for user {user_id}: {is_member} (status: {member.status})")
        return is_member
    except Exception as e:
        logging.error(f"Error checking channel membership for user {user_id}: {e}")
        return False


@dp.callback_query(lambda c: c.data == "textbooks")
async def process_textbooks(callback: types.CallbackQuery):
    """Обработчик входа в раздел учебников"""
    try:
        await callback.answer()

        message_text = f"""📚 Для доступа к учебникам необходимо:

1️⃣ Вступить в нашу группу: [Ссылка на группу]({GROUP_LINK})
2️⃣ Подписаться на канал: {CHANNEL_ID}

После выполнения условий нажмите кнопку "Проверить доступ" ⬇️"""

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Проверить доступ", callback_data="check_textbooks_access")
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


@dp.callback_query(lambda c: c.data == "check_textbooks_access")
async def check_textbooks_access(callback: types.CallbackQuery):
    """Обработчик проверки доступа к учебникам"""
    try:
        await callback.answer()
        user_id = callback.from_user.id

        logging.info(f"Checking access for user {user_id}")

        is_group_member = await check_group_membership(user_id)
        is_channel_member = await check_channel_membership(user_id)

        logging.info(
            f"Membership check results for user {user_id}: group={is_group_member}, channel={is_channel_member}")

        if not is_group_member or not is_channel_member:
            missing_items = []
            if not is_group_member:
                missing_items.append("группу")
            if not is_channel_member:
                missing_items.append("канал")

            message_text = f"""❌ Вы еще не подписались на {', '.join(missing_items)}!

📢 Для доступа к учебникам необходимо:
1️⃣ Вступить в нашу группу: [Ссылка на группу]({GROUP_LINK})
2️⃣ Подписаться на канал: {CHANNEL_ID}

Пожалуйста, подпишитесь и нажмите кнопку "Проверить доступ" снова."""

            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Проверить доступ", callback_data="check_textbooks_access")
            builder.button(text="⬅️ В главное меню", callback_data="back_to_main")
            builder.adjust(1)

        else:
            message_text = f"""✅ Поздравляем! 

📚 Вот ссылка на все учебники: [Яндекс.Диск]({YANDEX_DISK_LINK})

⚠️ Пожалуйста, не делитесь этой ссылкой с другими пользователями."""

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
