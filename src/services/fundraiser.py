from datetime import datetime

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
from src.database import Fundraiser, FundraiserRepository, FundraiserStatus, async_session
from src.keyboards import get_donate_keyboard


def render_progress_message(f: Fundraiser) -> str:
    percent, bar = calc_progress(f.current_amount, f.target_amount)
    lines = [
        '📹 <b>{}</b>'.format(escape_html(f.title or 'Сбор')),
        '',
        f'{bar} <b>{percent}%</b>',
        f'{format_amount(f.current_amount)} ₽ / {format_amount(f.target_amount)} ₽',
        '',
        f'📅 {format_date_moscow(f.start_date)} — {format_date_moscow(f.end_date)}',
    ]
    return '\n'.join(lines)


def render_completed_message(f: Fundraiser) -> str:
    percent, bar = calc_progress(f.current_amount, f.target_amount)
    return (
        '🎉 <b>Сбор завершён!</b>\n\n'
        f'<b>{escape_html(f.title or "")}</b>\n'
        f'{bar} <b>{percent}%</b>\n'
        f'Собрано: <b>{format_amount(f.current_amount)} ₽</b> из {format_amount(f.target_amount)} ₽\n\n'
        'Спасибо всем, кто участвовал!'
    )


class FundraiserService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def create_and_publish(
        self,
        *,
        target_amount: int,
        start_date: datetime,
        end_date: datetime,
        count_donations_from: datetime,
        title: str | None = None,
    ) -> Fundraiser:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            initial = await repo.get_donations_sum_from_date(count_donations_from)

            f = await repo.create(
                target_amount=target_amount,
                start_date=start_date,
                end_date=end_date,
                count_donations_from=count_donations_from,
                title=title,
            )
            if initial > 0:
                await repo.update_amount(f.id, initial)
                f.current_amount = initial

        text = render_progress_message(f)
        msg = await self.bot.send_message(
            chat_id=env.tribute.alert_group_id,
            message_thread_id=env.tribute.fundraiser_topic_id,
            text=text,
            reply_markup=get_donate_keyboard(env.tribute.donate_link),
        )
        await self.bot.pin_chat_message(
            chat_id=env.tribute.alert_group_id,
            message_id=msg.message_id,
            disable_notification=True,
        )

        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.set_message_id(f.id, msg.message_id)

        logger.info('Fundraiser published: id={}, message_id={}', f.id, msg.message_id)
        return f

    async def update_progress(self, amount: int) -> None:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.get_active()
            if not f:
                return

            f = await repo.add_amount(f.id, amount)
            if not f or not f.channel_message_id:
                return

            try:
                await self.bot.edit_message_text(
                    chat_id=env.tribute.alert_group_id,
                    message_id=f.channel_message_id,
                    text=render_progress_message(f),
                    reply_markup=get_donate_keyboard(env.tribute.donate_link),
                )
            except TelegramAPIError as e:
                logger.warning('Failed to update progress message: {}', e)

            if f.current_amount >= f.target_amount:
                await self.close_fundraiser(f.id, FundraiserStatus.COMPLETED)

    async def close_fundraiser(
        self,
        fundraiser_id: int,
        status: str = FundraiserStatus.COMPLETED,
    ) -> None:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            f = await repo.close(fundraiser_id, status)
            if not f:
                return

            if f.channel_message_id:
                try:
                    await self.bot.edit_message_text(
                        chat_id=env.tribute.alert_group_id,
                        message_id=f.channel_message_id,
                        text=render_completed_message(f),
                    )
                    await self.bot.unpin_chat_message(
                        chat_id=env.tribute.alert_group_id,
                        message_id=f.channel_message_id,
                    )
                except TelegramAPIError as e:
                    logger.warning('Failed to close pinned message: {}', e)

            try:
                await self.bot.send_message(
                    chat_id=env.tribute.alert_group_id,
                    text=render_completed_message(f),
                )
            except TelegramAPIError as e:
                logger.warning('Failed to send completion message: {}', e)

            await self._notify_admins(f, status)
            logger.info('Fundraiser closed: id={}, status={}', fundraiser_id, status)

    async def _notify_admins(self, f: Fundraiser, status: str) -> None:
        if status == FundraiserStatus.COMPLETED and f.current_amount >= f.target_amount:
            reason = 'цель достигнута'
        elif status == FundraiserStatus.COMPLETED:
            reason = 'истёк срок'
        else:
            reason = 'закрыт вручную'

        text = (
            f'ℹ️ Сбор #{f.id} закрыт ({reason}).\n'
            f'Собрано: {format_amount(f.current_amount)} ₽ '
            f'из {format_amount(f.target_amount)} ₽'
        )
        for admin_id in env.admin.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=text)
            except TelegramAPIError as e:
                logger.warning('Failed to notify admin {}: {}', admin_id, e)

    async def check_and_close_expired(self) -> None:
        now = datetime.now(MOSCOW_TZ)
        async with async_session() as session:
            repo = FundraiserRepository(session)
            expired = await repo.get_expired_active(now)
            for f in expired:
                await self.close_fundraiser(f.id, FundraiserStatus.COMPLETED)
