from datetime import datetime

from sqlalchemy import TIMESTAMP, BigInteger
from sqlmodel import Field, SQLModel

from .mixins import TimestampMixin


class Donation(TimestampMixin, SQLModel, table=True):
    __tablename__ = 'donations'

    id: int | None = Field(default=None, primary_key=True)
    tribute_donation_request_id: int = Field(sa_type=BigInteger, index=True)
    tribute_event_created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True), unique=True, index=True
    )
    telegram_user_id: int | None = Field(default=None, sa_type=BigInteger, index=True)
    username: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=256)
    amount: int = Field(sa_type=BigInteger)
    currency: str = Field(default='rub', index=True, max_length=3)
    comment: str | None = Field(default=None)
    is_anonymous: bool = Field(default=False, index=True)
