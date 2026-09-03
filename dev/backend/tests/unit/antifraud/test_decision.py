from decimal import Decimal

import pytest

from app.features.antifraud import scoring
from app.features.antifraud.models import FraudDecisionKind
from tests.unit.antifraud.data import receipt_ctx

DECISION_CASES: list[tuple[float, int, FraudDecisionKind]] = [
    (0.85, 1, "hold"),
    (0.85, 2, "block"),
    (0.6, 0, "hold"),
    (0.3, 0, "approve"),
]


@pytest.mark.parametrize(("score", "strong_count", "expected"), DECISION_CASES)
def test_decide_matches_domain_rules_examples(
    score: float, strong_count: int, expected: FraudDecisionKind
) -> None:
    assert scoring.decide(score, strong_count) == expected


def test_single_weak_signal_score_030_approves() -> None:
    ctx = receipt_ctx(pos_receipts_sample_size=10, max_pos_share_last_7d=Decimal("0.8"))

    decision = scoring.score_receipt(ctx)

    assert decision.score == pytest.approx(0.30)
    assert decision.decision == "approve"


def test_one_strong_and_two_weak_signals_score_060_holds() -> None:
    ctx = receipt_ctx(
        receipts_same_store_last_60min=4,
        frequency_per_week=Decimal("1"),
        receipts_last_7d=4,
        consecutive_matching_baskets=3,
    )

    decision = scoring.score_receipt(ctx)

    assert decision.score == pytest.approx(0.60)
    assert sum(1 for s in decision.signals if s.strong) == 1
    assert decision.decision == "hold"


def test_two_strong_signals_score_085_blocks() -> None:
    ctx = receipt_ctx(
        receipts_today=6,
        pos_receipts_sample_size=10,
        max_pos_share_last_7d=Decimal("0.8"),
        frequency_per_week=Decimal("1"),
        receipts_last_7d=4,
    )

    decision = scoring.score_receipt(ctx)

    assert decision.score == pytest.approx(0.85)
    assert sum(1 for s in decision.signals if s.strong) == 2
    assert decision.decision == "block"
