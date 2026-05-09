from datetime import datetime

from aiogram import Bot
from loguru import logger

from src.api.types import DonationPayload
from src.common import env, get_user_display_name
from src.database import DonationRepository, async_session


class DonationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def save(
        self, payload: DonationPayload, event_created_at: datetime
    ) -> tuple[bool, bool]:
        """Возвращает (saved_now, is_anonymous).

        saved_now=False — retry того же события (дедуп по tribute_event_created_at).
        Разные платежи через одну донат-страницу имеют общий donation_request_id,
        но разный event_created_at, поэтому каждый сохраняется как отдельная запись.
        """
        is_anonymous = payload.anonymously or not payload.telegram_user_id

        username = None
        full_name = None
        if payload.telegram_user_id and not is_anonymous:
            username, full_name = await get_user_display_name(
                self.bot, env.tribute.alert_group_id, payload.telegram_user_id
            )
            if username is None:
                username = payload.telegram_username

        async with async_session() as session:
            repo = DonationRepository(session)
            saved = await repo.add_donation(
                tribute_donation_request_id=payload.donation_request_id,
                tribute_event_created_at=event_created_at,
                amount=payload.amount,
                currency=payload.currency.lower(),
                telegram_user_id=payload.telegram_user_id,
                username=username,
                full_name=full_name,
                comment=payload.message,
                is_anonymous=is_anonymous,
            )

            if saved is None:
                logger.info(
                    'Duplicate webhook ignored: event_created_at={}, donation_request_id={}',
                    event_created_at.isoformat(),
                    payload.donation_request_id,
                )
                return False, is_anonymous

            logger.info(
                'Donation saved: id={}, amount={}, anon={}, event_created_at={}',
                saved.id,
                payload.amount,
                is_anonymous,
                event_created_at.isoformat(),
            )
            return True, is_anonymous
