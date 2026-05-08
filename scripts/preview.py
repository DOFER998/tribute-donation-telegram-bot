"""Send all group-facing messages to the configured chat for visual review."""
import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from src.common import MOSCOW_TZ, env, render
from src.keyboards import get_donate_keyboard
from src.services.digest import _ANNOUNCEMENT_IMAGE, render_announcement
from src.services.fundraiser import (
    render_completed_message,
    render_fundraiser_announcement,
    render_progress_message,
)


def _mock_fundraiser(current: int = 24000000) -> SimpleNamespace:
    now = datetime.now(MOSCOW_TZ)
    return SimpleNamespace(
        id=0,
        title='Камеры для 1 корпуса',
        target_amount=69800000,
        current_amount=current,
        start_date=now,
        end_date=now + timedelta(days=30),
    )


async def _send(bot: Bot, label: str, *, text: str, with_button: bool = True) -> None:
    markup = get_donate_keyboard(env.tribute.donate_link) if with_button else None
    await bot.send_message(
        chat_id=env.tribute.alert_group_id,
        message_thread_id=env.tribute.alert_topic_id,
        text=text,
        reply_markup=markup,
    )
    print(f'✓ {label}')


async def main() -> None:
    bot = Bot(
        token=env.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        fundraiser = _mock_fundraiser()
        completed = _mock_fundraiser(current=70000000)

        # 1. Анонс старта сбора
        await _send(
            bot,
            'Fundraiser announcement (start)',
            text=await render_fundraiser_announcement(fundraiser),
        )

        # 2. Закреплённое сообщение прогресса
        await _send(
            bot,
            'Pinned progress message',
            text=await render_progress_message(fundraiser),
        )

        # 3. Алерт о новом взносе
        await _send(
            bot,
            'Donation alert',
            text=await render(
                'donation_alert.html.j2',
                display_name='Иван Иванов',
                amount_kopecks=200000,
                comment='За безопасность дома!',
            ),
        )

        # 4. Ежедневный пост-напоминание (фото + caption)
        await bot.send_photo(
            chat_id=env.tribute.alert_group_id,
            message_thread_id=env.tribute.alert_topic_id,
            photo=FSInputFile(_ANNOUNCEMENT_IMAGE),
            caption=await render_announcement(fundraiser),
            reply_markup=get_donate_keyboard(env.tribute.donate_link),
        )
        print('✓ Daily announcement (photo + caption)')

        # 5. Сообщение о завершении сбора (без кнопки)
        await _send(
            bot,
            'Fundraiser completed',
            text=await render_completed_message(completed),
            with_button=False,
        )

    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
