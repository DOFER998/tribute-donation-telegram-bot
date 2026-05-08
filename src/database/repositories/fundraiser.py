from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Donation, Fundraiser, FundraiserStatus


class FundraiserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        target_amount: int,
        start_date: datetime,
        end_date: datetime,
        count_donations_from: datetime,
        title: str | None = None,
    ) -> Fundraiser:
        fundraiser = Fundraiser(
            title=title,
            target_amount=target_amount,
            start_date=start_date,
            end_date=end_date,
            count_donations_from=count_donations_from,
        )
        self.session.add(fundraiser)
        await self.session.commit()
        await self.session.refresh(fundraiser)
        return fundraiser

    async def get_active(self) -> Fundraiser | None:
        q = select(Fundraiser).where(Fundraiser.status == FundraiserStatus.ACTIVE)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_id(self, fundraiser_id: int) -> Fundraiser | None:
        q = select(Fundraiser).where(Fundraiser.id == fundraiser_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def update_amount(self, fundraiser_id: int, amount: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.current_amount = amount
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def add_amount(self, fundraiser_id: int, delta: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.current_amount += delta
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def set_message_id(self, fundraiser_id: int, message_id: int) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.channel_message_id = message_id
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def close(
        self, fundraiser_id: int, status: str = FundraiserStatus.COMPLETED
    ) -> Fundraiser | None:
        f = await self.get_by_id(fundraiser_id)
        if f:
            f.status = status
            await self.session.commit()
            await self.session.refresh(f)
        return f

    async def get_donations_sum_from_date(self, from_date: datetime) -> int:
        q = select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.created_at >= from_date
        )
        return (await self.session.execute(q)).scalar() or 0

    async def get_expired_active(self, now: datetime) -> list[Fundraiser]:
        q = select(Fundraiser).where(
            Fundraiser.status == FundraiserStatus.ACTIVE, Fundraiser.end_date <= now
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
