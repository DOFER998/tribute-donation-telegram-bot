from datetime import datetime

from sqlalchemy import TIMESTAMP
from sqlmodel import Field

from src.common import utc_now


class TimestampMixin:
    created_at: datetime = Field(
        default_factory=utc_now, sa_type=TIMESTAMP(timezone=True), index=True
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={'onupdate': utc_now},
    )
