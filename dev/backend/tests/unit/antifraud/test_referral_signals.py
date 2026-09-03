import pytest

from app.features.antifraud import scoring
from tests.unit.antifraud.data import REFERRAL_SIGNAL_CASES, referral_ctx

TRIGGERED_CASES = [(code, kwargs) for code, kwargs, expected in REFERRAL_SIGNAL_CASES if expected]


@pytest.mark.parametrize(("code", "kwargs", "expected"), REFERRAL_SIGNAL_CASES)
def test_referral_signal_fires_at_boundary(
    code: str, kwargs: dict[str, object], expected: bool
) -> None:
    decision = scoring.score_referral(referral_ctx(**kwargs))
    codes = {signal.code for signal in decision.signals}
    assert (code in codes) is expected


@pytest.mark.parametrize(("code", "kwargs"), TRIGGERED_CASES)
def test_referral_signal_detail_has_numbers(code: str, kwargs: dict[str, object]) -> None:
    decision = scoring.score_referral(referral_ctx(**kwargs))
    signal = next(s for s in decision.signals if s.code == code)
    assert any(ch.isdigit() for ch in signal.detail)
