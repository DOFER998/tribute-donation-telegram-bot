from unittest.mock import MagicMock

import pytest

from src.services.digest import render_digest


@pytest.mark.asyncio
async def test_render_digest_no_fundraiser_no_top():
    today = {'total_amount': 0, 'count': 0, 'unique_donors': 0}
    text = await render_digest(today, None, [])
    assert '📊' in text
    assert 'Собрано: 0 ₽' in text


@pytest.mark.asyncio
async def test_render_digest_with_fundraiser_and_top():
    today = {'total_amount': 200000, 'count': 1, 'unique_donors': 1}
    fundraiser = MagicMock()
    fundraiser.current_amount = 200000
    fundraiser.target_amount = 1000000
    top = [
        {'telegram_user_id': 1, 'username': 'a', 'full_name': 'Alice', 'total_amount': 200000},
    ]
    text = await render_digest(today, fundraiser, top)
    assert 'Топ-3' in text
    assert 'Alice' in text
    assert '20%' in text
