import pytest

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.services.dashboard import delta, period_label


def test_delta_modes():
    s = [{"value": 4.0}, {"value": 5.0}]
    assert delta(s, "pp") == 1.0 and delta(s, "pct") == 25.0
    assert delta(s[:1], "pp") is None and delta([{"value": 0}, {"value": 1}], "pct") is None


def test_period_label():
    assert period_label("2024-25") == "FY25" and period_label("2024") == "2024"


def test_password_and_jwt_roundtrip():
    assert verify_password("correct horse", hash_password("correct horse"))
    assert not verify_password("nope", hash_password("correct horse"))
    s = get_settings()
    token, ttl = create_access_token(s, user_id="u1", role="viewer")
    assert decode_access_token(s, token).sub == "u1" and ttl == s.access_token_minutes * 60
    with pytest.raises(AuthenticationError):
        decode_access_token(s, token + "x")
