from datetime import UTC, datetime

from src.common.constants import MOSCOW_TZ


def utc_now() -> datetime:
    return datetime.now(UTC)


def format_date_moscow(dt: datetime) -> str:
    return dt.astimezone(MOSCOW_TZ).strftime('%d.%m.%Y')


def format_datetime_moscow(dt: datetime) -> str:
    return dt.astimezone(MOSCOW_TZ).strftime('%d.%m.%Y %H:%M')


def parse_date_msk(text: str) -> datetime | None:
    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(text.strip(), fmt)
            return dt.replace(tzinfo=MOSCOW_TZ)
        except ValueError:
            continue
    return None
