from decimal import Decimal

import pytest

from app.features.antifraud import scoring
from app.features.antifraud.models import FraudDecisionKind
from tests.unit.antifraud.data import receipt_ctx, referral_ctx

DECIDE_THRESHOLD_CASES: list[tuple[float, int, FraudDecisionKind]] = [
    (0.5, 0, "hold"),
    (0.499, 0, "approve"),
    (0.8, 2, "block"),
    (0.8, 1, "hold"),
    (0.79, 5, "hold"),
    (1.0, 2, "block"),
    (1.0, 0, "hold"),
]


@pytest.mark.parametrize(("score", "strong_count", "expected"), DECIDE_THRESHOLD_CASES)
def test_decide_threshold_boundaries(
    score: float, strong_count: int, expected: FraudDecisionKind
) -> None:
    assert scoring.decide(score, strong_count) == expected


def test_receipt_score_caps_at_one_when_all_six_signals_fire() -> None:
    ctx = receipt_ctx(
        receipts_same_store_last_60min=4,
        receipts_today=6,
        pos_receipts_sample_size=10,
        max_pos_share_last_7d=Decimal("0.8"),
        frequency_per_week=Decimal("1"),
        receipts_last_7d=4,
        is_return=True,
        days_since_challenge_completion_by_this_receipt=3,
        consecutive_matching_baskets=3,
    )

    decision = scoring.score_receipt(ctx)

    assert len(decision.signals) == 6
    assert decision.score == 1.0
    assert decision.decision == "block"


def test_referral_score_080_with_one_strong_signal_holds() -> None:
    ctx = referral_ctx(
        is_referral_ring=True,
        minutes_since_link_generated=5,
        invites_last_hour=6,
        days_since_qualifying_with_no_activity=14,
    )

    decision = scoring.score_referral(ctx)

    assert decision.score == 0.80
    assert sum(1 for s in decision.signals if s.strong) == 1
    assert decision.decision == "hold"


def test_referral_score_090_with_one_strong_signal_holds() -> None:
    ctx = referral_ctx(
        shared_device=True,
        minutes_since_link_generated=5,
        invites_last_hour=6,
        days_since_qualifying_with_no_activity=14,
    )

    decision = scoring.score_referral(ctx)

    assert decision.score == 0.90
    assert sum(1 for s in decision.signals if s.strong) == 1
    assert decision.decision == "hold"


def test_referral_score_085_with_two_strong_signals_blocks() -> None:
    ctx = referral_ctx(
        shared_device=True,
        invitees_count=3,
        invitees_all_single_purchase_500_550=True,
        minutes_since_link_generated=5,
    )

    decision = scoring.score_referral(ctx)

    assert decision.score == 0.85
    assert sum(1 for s in decision.signals if s.strong) == 2
    assert decision.decision == "block"
