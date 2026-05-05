from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.utils.jwt_utils import SECRET_KEY, decode_token


def _encode_token(iat_offset_seconds):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "test@example.com",
            "iat": now + timedelta(seconds=iat_offset_seconds),
            "exp": now + timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def test_decode_token_allows_small_clock_skew():
    token = _encode_token(iat_offset_seconds=1)

    payload = decode_token(token)

    assert payload["sub"] == "test@example.com"


def test_decode_token_rejects_large_clock_skew():
    token = _encode_token(iat_offset_seconds=30)

    with pytest.raises(jwt.ImmatureSignatureError):
        decode_token(token)
