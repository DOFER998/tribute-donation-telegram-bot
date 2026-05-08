import hashlib
import hmac
import json

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.routers import tribute as tribute_router
from src.api.utils.parser import parse_tribute_request


def _signed_body(secret: str, data: dict) -> tuple[bytes, str]:
    body = json.dumps(data).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(monkeypatch):
    from fastapi import FastAPI

    monkeypatch.setattr(
        'src.common.env.tribute.api_key.get_secret_value',
        lambda: 'secret',
    )

    app = FastAPI()
    app.include_router(tribute_router.router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        body, _ = _signed_body('wrong-secret', {'name': 'new_donation', 'payload': {}})
        resp = await client.post(
            '/tribute',
            content=body,
            headers={'trbt-signature': 'deadbeef'},
        )
        assert resp.status_code == 401


def test_parse_tribute_request_round_trip():
    """Smoke: парсер работает на реалистичном payload."""
    data = {
        'name': 'new_donation',
        'created_at': '2026-05-07T12:00:00Z',
        'sent_at': '2026-05-07T12:00:01Z',
        'payload': {
            'donation_request_id': 100,
            'donation_name': 'Камеры',
            'message': 'привет',
            'period': '',
            'amount': 200000,
            'currency': 'rub',
            'anonymously': False,
            'web_app_link': '',
            'telegram_user_id': 555,
        },
    }
    parsed = parse_tribute_request(data)
    assert parsed is not None
    assert parsed.payload['message'] == 'привет'
