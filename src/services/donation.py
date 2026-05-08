from aiogram import Bot
from loguru import logger

from src.api.types import DonationPayload
from src.common import env, get_user_display_name
from src.database import DonationRepository, async_session


class DonationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def save(self, payload: DonationPayload) -> tuple[bool, bool]:
        """
        Returns (saved_now, is_anonymous).
        saved_now=False означает дубликат (идемпотентность).
        """
        is_anonymous = payload.anonymously or not payload.telegram_user_id

        username = None
        full_name = None
        if payload.telegram_user_id and not is_anonymous:
            username, full_name = await get_user_display_name(
                self.bot, env.tribute.alert_group_id, payload.telegram_user_id
            )

        async with async_session() as session:
            repo = DonationRepository(session)
            saved = await repo.add_donation(
                tribute_donation_request_id=payload.donation_request_id,
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
                    'Duplicate webhook ignored: donation_request_id={}',
                    payload.donation_request_id,
                )
                return False, is_anonymous

            logger.info(
                'Donation saved: id={}, amount={}, anon={}',
                saved.id,
                payload.amount,
                is_anonymous,
            )
            return True, is_anonymous
