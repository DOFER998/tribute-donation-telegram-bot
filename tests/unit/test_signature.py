import hashlib
import hmac

from src.api.utils.signature import verify_tribute_signature


SECRET = 'test-secret'


def _sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    body = b'{"name":"new_donation"}'
    sig = _sign(body)
    assert verify_tribute_signature(body, sig, SECRET) is True


def test_invalid_signature_returns_false():
    body = b'{"name":"new_donation"}'
    assert verify_tribute_signature(body, 'deadbeef', SECRET) is False


def test_missing_signature_returns_false():
    body = b'{"name":"new_donation"}'
    assert verify_tribute_signature(body, None, SECRET) is False


def test_wrong_secret_returns_false():
    body = b'{"name":"new_donation"}'
    sig = _sign(body, 'other-secret')
    assert verify_tribute_signature(body, sig, SECRET) is False


def test_tampered_body_returns_false():
    body = b'{"name":"new_donation"}'
    sig = _sign(body)
    assert verify_tribute_signature(b'{"name":"hacked"}', sig, SECRET) is False
