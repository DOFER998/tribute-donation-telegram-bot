from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.common import MOSCOW_TZ, env, format_date_moscow, render
from src.database import Fundraiser, FundraiserRepository, FundraiserStatus, async_session
from src.keyboards import get_donate_keyboard


def require_fundraiser_id(fundraiser: Fundraiser) -> int:
    if fundraiser.id is None:
        raise RuntimeError('fundraiser is not persisted (id is None)')
    return fundraiser.id


async def render_progress_message(fundraiser: Fundraiser) -> str:
    remaining = max(fundraiser.target_amount - fundraiser.current_amount, 0)
    return await render(
        'fundraiser_progress.html.j2',
        fundraiser=fundraiser,
        remaining=remaining,
        start_date=format_date_moscow(fundraiser.start_date),
        end_date=format_date_moscow(fundraiser.end_date),
    )


async def render_fundraiser_announcement(fundraiser: Fundraiser) -> str:
    return await render(
        'fundraiser_announcement.html.j2',
        fundraiser=fundraiser,
        end_date=format_date_moscow(fundraiser.end_date),
    )


async def render_completed_message(fundraiser: Fundraiser) -> str:
    return await render('fundraiser_completed.html.j2', fundraiser=fundraiser)


async def render_admin_close_message(fundraiser: Fundraiser, reason: str) -> str:
    return await render('fundraiser_admin_close.html.j2', fundraiser=fundraiser, reason=reason)


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
            fundraiser_id = require_fundraiser_id(f)
            if initial > 0:
                await repo.update_amount(fundraiser_id, initial)
                f.current_amount = initial

        await self.bot.send_message(
            chat_id=env.tribute.alert_group_id,
            message_thread_id=env.tribute.fundraiser_topic_id,
            text=await render_fundraiser_announcement(f),
            reply_markup=get_donate_keyboard(env.tribute.donate_link),
        )

        progress_text = await render_progress_message(f)
        msg = await self.bot.send_message(
            chat_id=env.tribute.alert_group_id,
            message_thread_id=env.tribute.fundraiser_topic_id,
            text=progress_text,
            reply_markup=get_donate_keyboard(env.tribute.donate_link),
        )
        await self.bot.pin_chat_message(
            chat_id=env.tribute.alert_group_id,
            message_id=msg.message_id,
            disable_notification=True,
        )

        async with async_session() as session:
            repo = FundraiserRepository(session)
            updated = await repo.set_message_id(fundraiser_id, msg.message_id)
            if updated is None:
                raise RuntimeError(f'fundraiser {fundraiser_id} disappeared after creation')

        logger.info('Fundraiser published: id={}, message_id={}', updated.id, msg.message_id)
        return updated

    async def update_progress(self, amount: int) -> None:
        async with async_session() as session:
            repo = FundraiserRepository(session)
            active = await repo.get_active()
            if not active:
                return

            active_id = require_fundraiser_id(active)
            updated = await repo.add_amount(active_id, amount)
            if not updated or not updated.channel_message_id:
                return

            try:
                await self.bot.edit_message_text(
                    chat_id=env.tribute.alert_group_id,
                    message_id=updated.channel_message_id,
                    text=await render_progress_message(updated),
                    reply_markup=get_donate_keyboard(env.tribute.donate_link),
                )
            except TelegramAPIError as e:
                logger.warning('Failed to update progress message: {}', e)

            if updated.current_amount >= updated.target_amount:
                await self.close_fundraiser(
                    require_fundraiser_id(updated), FundraiserStatus.COMPLETED
                )

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

            completed_text = await render_completed_message(f)

            if f.channel_message_id:
                try:
                    await self.bot.edit_message_text(
                        chat_id=env.tribute.alert_group_id,
                        message_id=f.channel_message_id,
                        text=completed_text,
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
                    text=completed_text,
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

        text = await render_admin_close_message(f, reason)
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
                await self.close_fundraiser(require_fundraiser_id(f), FundraiserStatus.COMPLETED)
