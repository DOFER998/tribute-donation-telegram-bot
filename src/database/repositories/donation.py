from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Donation


class DonationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_donation(
        self,
        *,
        tribute_donation_request_id: int,
        amount: int,
        currency: str = 'rub',
        telegram_user_id: int | None = None,
        username: str | None = None,
        full_name: str | None = None,
        comment: str | None = None,
        is_anonymous: bool = False,
    ) -> Donation | None:
        """Идемпотентная вставка. Возвращает None если запись уже была."""
        stmt = (
            pg_insert(Donation.__table__)
            .values(
                tribute_donation_request_id=tribute_donation_request_id,
                telegram_user_id=telegram_user_id,
                username=username,
                full_name=full_name,
                amount=amount,
                currency=currency,
                comment=comment,
                is_anonymous=is_anonymous,
            )
            .on_conflict_do_nothing(index_elements=['tribute_donation_request_id'])
            .returning(Donation.__table__)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        row = result.first()
        if row is None:
            return None
        return Donation(**dict(row._mapping))

    async def get_all(self) -> list[Donation]:
        result = await self.session.execute(
            select(Donation).order_by(Donation.created_at.desc())
        )
        return list(result.scalars().all())
