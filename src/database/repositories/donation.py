from datetime import datetime

from sqlalchemy import func, select
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

    async def get_user_total(self, telegram_user_id: int) -> int:
        query = select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.telegram_user_id == telegram_user_id,
            Donation.is_anonymous.is_(False),
        )
        return (await self.session.execute(query)).scalar() or 0

    async def get_user_rank(self, telegram_user_id: int) -> int | None:
        user_total = await self.get_user_total(telegram_user_id)
        if user_total == 0:
            return None

        subquery = (
            select(
                Donation.telegram_user_id,
                func.sum(Donation.amount).label('total'),
            )
            .where(
                Donation.is_anonymous.is_(False),
                Donation.telegram_user_id.isnot(None),
            )
            .group_by(Donation.telegram_user_id)
            .subquery()
        )
        rank_query = select(func.count()).where(subquery.c.total > user_total)
        users_above = (await self.session.execute(rank_query)).scalar() or 0
        return users_above + 1

    async def get_top_donors(self, limit: int = 3) -> list[dict]:
        query = (
            select(
                Donation.telegram_user_id,
                func.max(Donation.username).label('username'),
                func.max(Donation.full_name).label('full_name'),
                func.sum(Donation.amount).label('total_amount'),
            )
            .where(
                Donation.is_anonymous.is_(False),
                Donation.telegram_user_id.isnot(None),
            )
            .group_by(Donation.telegram_user_id)
            .order_by(func.sum(Donation.amount).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [
            {
                'telegram_user_id': r.telegram_user_id,
                'username': r.username,
                'full_name': r.full_name,
                'total_amount': r.total_amount,
            }
            for r in result.all()
        ]

    async def get_stats_for_period(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> dict:
        conds = []
        if start:
            conds.append(Donation.created_at >= start)
        if end:
            conds.append(Donation.created_at < end)

        total = (
            await self.session.execute(
                select(func.coalesce(func.sum(Donation.amount), 0)).where(*conds)
            )
        ).scalar() or 0
        count = (
            await self.session.execute(select(func.count()).where(*conds))
        ).scalar() or 0
        unique = (
            await self.session.execute(
                select(func.count(func.distinct(Donation.telegram_user_id))).where(
                    Donation.telegram_user_id.isnot(None),
                    Donation.is_anonymous.is_(False),
                    *conds,
                )
            )
        ).scalar() or 0
        return {'total_amount': total, 'count': count, 'unique_donors': unique}

    async def get_all(self) -> list[Donation]:
        result = await self.session.execute(
            select(Donation).order_by(Donation.created_at.desc())
        )
        return list(result.scalars().all())
