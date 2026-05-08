"""Send a sample donation alert and a daily announcement to the configured chat."""
import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from src.common import MOSCOW_TZ, env, render
from src.database import FundraiserRepository, async_session
from src.keyboards import get_donate_keyboard
from src.services.digest import _ANNOUNCEMENT_IMAGE, render_announcement


async def _send_donation_alert(bot: Bot) -> None:
    text = await render(
        'donation_alert.html.j2',
        display_name='Иван Иванов',
        amount_kopecks=200000,
        comment='За безопасность дома!',
    )
    await bot.send_message(
        chat_id=env.tribute.alert_group_id,
        message_thread_id=env.tribute.alert_topic_id,
        text=text,
        reply_markup=get_donate_keyboard(env.tribute.donate_link),
    )
    print('✓ Donation alert sent')


async def _send_daily_announcement(bot: Bot) -> None:
    async with async_session() as session:
        fundraiser = await FundraiserRepository(session).get_active()

    if fundraiser is None:
        now = datetime.now(MOSCOW_TZ)
        fundraiser = SimpleNamespace(
            id=0,
            title='Камеры для 1 корпуса',
            target_amount=69800000,
            current_amount=24000000,
            start_date=now,
            end_date=now + timedelta(days=30),
        )
        print('  (no active fundraiser in DB, using mock for preview)')

    caption = await render_announcement(fundraiser)
    photo = FSInputFile(_ANNOUNCEMENT_IMAGE)

    await bot.send_photo(
        chat_id=env.tribute.alert_group_id,
        message_thread_id=env.tribute.alert_topic_id,
        photo=photo,
        caption=caption,
        reply_markup=get_donate_keyboard(env.tribute.donate_link),
    )
    print('✓ Daily announcement sent')


async def main() -> None:
    bot = Bot(
        token=env.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await _send_donation_alert(bot)
        await _send_daily_announcement(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
