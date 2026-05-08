import pytest

from src.database.repositories.donation import DonationRepository


@pytest.mark.asyncio
async def test_add_donation_returns_record(db_session):
    repo = DonationRepository(db_session)
    d = await repo.add_donation(
        tribute_donation_request_id=42,
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
async def test_add_donation_idempotent(db_session):
    repo = DonationRepository(db_session)
    first = await repo.add_donation(tribute_donation_request_id=43, amount=100000)
    second = await repo.add_donation(tribute_donation_request_id=43, amount=999999)
    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_get_all_returns_all_donations(db_session):
    repo = DonationRepository(db_session)
    await repo.add_donation(tribute_donation_request_id=1, amount=300000, telegram_user_id=1)
    await repo.add_donation(tribute_donation_request_id=2, amount=100000, is_anonymous=True)
    rows = await repo.get_all()
    assert len(rows) == 2
