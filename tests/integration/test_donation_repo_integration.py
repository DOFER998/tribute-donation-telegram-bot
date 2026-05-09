from datetime import UTC, datetime

import pytest

from src.database.repositories.donation import DonationRepository


def _ts(seconds: int) -> datetime:
    return datetime(2026, 5, 9, 12, 0, seconds, tzinfo=UTC)


@pytest.mark.asyncio
async def test_add_donation_returns_record(db_session):
    repo = DonationRepository(db_session)
    d = await repo.add_donation(
        tribute_donation_request_id=42,
        tribute_event_created_at=_ts(0),
        amount=200000,
        telegram_user_id=999,
        username='alice',
        full_name='Alice Wonderland',
        comment='удачи',
    )
    assert d is not None
    assert d.amount == 200000
    assert d.username == 'alice'


@pytest.mark.asyncio
async def test_add_donation_idempotent_on_same_event(db_session):
    """Retry того же события (same event_created_at) → вторая вставка отбрасывается."""
    repo = DonationRepository(db_session)
    ts = _ts(1)
    first = await repo.add_donation(
        tribute_donation_request_id=43, tribute_event_created_at=ts, amount=100000
    )
    second = await repo.add_donation(
        tribute_donation_request_id=43, tribute_event_created_at=ts, amount=999999
    )
    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_add_donation_allows_same_request_id_different_events(db_session):
    """Разные платежи через одну донат-страницу: same donation_request_id, разный event_created_at."""
    repo = DonationRepository(db_session)
    first = await repo.add_donation(
        tribute_donation_request_id=44, tribute_event_created_at=_ts(2), amount=100000
    )
    second = await repo.add_donation(
        tribute_donation_request_id=44, tribute_event_created_at=_ts(3), amount=200000
    )
    assert first is not None
    assert second is not None
    assert first.id != second.id


@pytest.mark.asyncio
async def test_get_all_returns_all_donations(db_session):
    repo = DonationRepository(db_session)
    await repo.add_donation(
        tribute_donation_request_id=1,
        tribute_event_created_at=_ts(4),
        amount=300000,
        telegram_user_id=1,
    )
    await repo.add_donation(
        tribute_donation_request_id=2,
        tribute_event_created_at=_ts(5),
        amount=100000,
        is_anonymous=True,
    )
    rows = await repo.get_all()
    assert len(rows) == 2
