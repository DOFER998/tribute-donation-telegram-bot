from datetime import datetime

from sqlalchemy import TIMESTAMP, BigInteger
from sqlmodel import Field, SQLModel

from .mixins import TimestampMixin


class FundraiserStatus:
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Fundraiser(TimestampMixin, SQLModel, table=True):
    __tablename__ = 'fundraisers'

    id: int | None = Field(default=None, primary_key=True)
    title: str | None = Field(default=None)
    target_amount: int = Field(sa_type=BigInteger)
    current_amount: int = Field(default=0, sa_type=BigInteger)
    start_date: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    end_date: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    count_donations_from: datetime = Field(sa_type=TIMESTAMP(timezone=True))
    channel_message_id: int | None = Field(default=None, sa_type=BigInteger)
    status: str = Field(default=FundraiserStatus.ACTIVE, index=True)
