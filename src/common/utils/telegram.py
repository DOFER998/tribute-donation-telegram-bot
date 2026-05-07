from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger


async def get_user_display_name(bot: Bot, chat_id: int, user_id: int) -> tuple[str | None, str | None]:
    """Вернуть (username, full_name) для пользователя в чате. None если не удалось получить."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except TelegramAPIError as e:
        logger.warning('Failed to get chat member: chat_id={}, user_id={}, err={}', chat_id, user_id, e)
        return None, None
    user = member.user
    return user.username, user.full_name
