from datetime import datetime, time, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.common import MOSCOW_TZ, env, format_date_moscow, render
from src.database import DonationRepository, Fundraiser, FundraiserRepository, async_session


def _today_window() -> tuple[datetime, datetime]:
    now = datetime.now(MOSCOW_TZ)
    today_start = datetime.combine(now.date(), time.min, tzinfo=MOSCOW_TZ)
    today_end = today_start + timedelta(days=1)
    return today_start, today_end


def _donor_display_name(donor: dict) -> str:
    return donor.get('full_name') or (
        f'@{donor["username"]}' if donor.get('username') else 'без имени'
    )


async def render_digest(
    today_stats: dict,
    fundraiser: Fundraiser | None,
    top: list[dict],
) -> str:
    today_start, _ = _today_window()
    remaining = (
        max(fundraiser.target_amount - fundraiser.current_amount, 0) if fundraiser else 0
    )
    top_display = [
        {**donor, 'display_name': _donor_display_name(donor)} for donor in top
    ]
    return await render(
        'daily_digest.html.j2',
        today_date=format_date_moscow(today_start),
        today=today_stats,
        fundraiser=fundraiser,
        remaining=remaining,
        top=top_display,
    )


class DigestService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_daily(self) -> None:
        start, end = _today_window()
        async with async_session() as session:
            d_repo = DonationRepository(session)
            f_repo = FundraiserRepository(session)
            today_stats = await d_repo.get_stats_for_period(start=start, end=end)
            top = await d_repo.get_top_donors(limit=3)
            fundraiser = await f_repo.get_active()

        text = await render_digest(today_stats, fundraiser, top)

        for admin_id in env.admin.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=text)
            except TelegramAPIError as e:
                logger.warning('Failed to DM admin {}: {}', admin_id, e)

        logger.info('Daily digest sent to {} admins', len(env.admin.admin_ids))


__all__ = ['DigestService', 'render_digest']
