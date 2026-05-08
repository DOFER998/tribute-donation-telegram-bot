from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile
from loguru import logger

from src.common import env, render
from src.database import Fundraiser, FundraiserRepository, async_session
from src.keyboards import get_donate_keyboard

_ANNOUNCEMENT_IMAGE = Path(__file__).parent.parent / 'static' / 'announcement.jpg'


async def render_announcement(fundraiser: Fundraiser) -> str:
    remaining = max(fundraiser.target_amount - fundraiser.current_amount, 0)
    return await render(
        'daily_announcement.html.j2',
        fundraiser=fundraiser,
        remaining=remaining,
    )


class DigestService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_daily(self) -> None:
        async with async_session() as session:
            fundraiser = await FundraiserRepository(session).get_active()

        if fundraiser is None:
            logger.info('Daily announcement skipped: no active fundraiser')
            return

        caption = await render_announcement(fundraiser)
        photo = FSInputFile(_ANNOUNCEMENT_IMAGE)

        try:
            await self.bot.send_photo(
                chat_id=env.tribute.alert_group_id,
                message_thread_id=fundraiser.topic_id,
                photo=photo,
                caption=caption,
                reply_markup=get_donate_keyboard(env.tribute.donate_link),
            )
        except TelegramAPIError as e:
            logger.warning('Failed to send daily announcement: {}', e)
            return

        logger.info(
            'Daily announcement sent: {} ₽ / {} ₽',
            fundraiser.current_amount,
            fundraiser.target_amount,
        )


__all__ = ['DigestService', 'render_announcement']
