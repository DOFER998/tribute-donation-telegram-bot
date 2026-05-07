from datetime import datetime, time, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.common import (
    MOSCOW_TZ,
    calc_progress,
    env,
    escape_html,
    format_amount,
    format_date_moscow,
)
from src.database import DonationRepository, FundraiserRepository, async_session


def _today_window() -> tuple[datetime, datetime]:
    now = datetime.now(MOSCOW_TZ)
    today_start = datetime.combine(now.date(), time.min, tzinfo=MOSCOW_TZ)
    today_end = today_start + timedelta(days=1)
    return today_start, today_end


def _format_top_donor(rank: int, d: dict) -> str:
    name = d.get('full_name') or (f'@{d["username"]}' if d.get('username') else 'без имени')
    return f'{rank}. {escape_html(name)} — {format_amount(d["total_amount"])} ₽'


def render_digest(today_stats: dict, fundraiser, top: list[dict]) -> str:
    today_start, _ = _today_window()
    lines = [
        f'📊 <b>Сводка за {format_date_moscow(today_start)}</b>',
        '',
        '<b>За сегодня:</b>',
        f'• Собрано: {format_amount(today_stats["total_amount"])} ₽',
        f'• Донатов: {today_stats["count"]}',
        f'• Уникальных: {today_stats["unique_donors"]}',
    ]

    if fundraiser:
        percent, bar = calc_progress(fundraiser.current_amount, fundraiser.target_amount)
        remaining = max(fundraiser.target_amount - fundraiser.current_amount, 0)
        lines += [
            '',
            '<b>Всего по сбору:</b>',
            f'• {format_amount(fundraiser.current_amount)} ₽ / {format_amount(fundraiser.target_amount)} ₽',
            f'• {bar} {percent}%',
            f'• Осталось: {format_amount(remaining)} ₽',
        ]

    if top:
        lines += ['', '<b>Топ-3:</b>']
        for i, donor in enumerate(top, 1):
            lines.append(_format_top_donor(i, donor))

    return '\n'.join(lines)


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

        text = render_digest(today_stats, fundraiser, top)

        for admin_id in env.admin.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=text)
            except TelegramAPIError as e:
                logger.warning('Failed to DM admin {}: {}', admin_id, e)

        logger.info('Daily digest sent to {} admins', len(env.admin.admin_ids))
