from unittest.mock import MagicMock

import pytest

from src.services.digest import render_announcement


@pytest.mark.asyncio
async def test_render_announcement_includes_progress_and_remaining():
    fundraiser = MagicMock()
    fundraiser.current_amount = 24000000
    fundraiser.target_amount = 69800000
    text = await render_announcement(fundraiser)
    assert 'Уважаемые соседи' in text
    assert 'Собрано: <b>240 000 ₽</b>' in text
    assert 'Осталось: <b>458 000 ₽</b>' in text
    assert '34%' in text
    assert 'этаж' in text
    assert 'квартиру' in text


@pytest.mark.asyncio
async def test_render_announcement_caption_fits_telegram_limit():
    fundraiser = MagicMock()
    fundraiser.current_amount = 0
    fundraiser.target_amount = 69800000
    text = await render_announcement(fundraiser)
    assert len(text) <= 1024


@pytest.mark.asyncio
async def test_render_announcement_handles_overshoot():
    fundraiser = MagicMock()
    fundraiser.current_amount = 70000000
    fundraiser.target_amount = 69800000
    text = await render_announcement(fundraiser)
    assert 'Осталось: <b>0 ₽</b>' in text
    assert '100%' in text
