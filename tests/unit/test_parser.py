from src.api.enums import TributeRequestType
from src.api.utils.parser import parse_tribute_request


def _valid_payload():
    return {
        'name': 'new_donation',
        'created_at': '2026-05-07T12:00:00Z',
        'sent_at': '2026-05-07T12:00:01Z',
        'payload': {
            'donation_request_id': 12345,
            'donation_name': 'Камеры для 1 корпуса',
            'message': 'удачи',
            'period': '',
            'amount': 200000,
            'currency': 'rub',
            'anonymously': False,
            'web_app_link': '',
            'telegram_user_id': 99,
        },
    }


def test_parse_valid_donation():
    req = parse_tribute_request(_valid_payload())
    assert req is not None
    assert req.name == TributeRequestType.NEW_DONATION
    assert req.payload.amount == 200000
    assert req.payload.message == 'удачи'


def test_parse_invalid_returns_none():
    assert parse_tribute_request({'foo': 'bar'}) is None


def test_parse_unknown_event_returns_none():
    data = _valid_payload()
    data['name'] = 'totally_unknown_event'
    assert parse_tribute_request(data) is None
