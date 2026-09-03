import pytest

from app.features.challenges.models import ChallengeProgressDelta
from app.features.receipts import outcome
from app.features.receipts.models import CountedDecision
from tests.unit.receipts.outcome_data import (
    APPROVE_DECISION,
    BLOCK_DECISION,
    DECISION_COUNTED,
    DOMOVOY_STATE,
    RANK,
    RECEIPT,
    XP_DELTA_ACHIEVEMENTS_CASES,
    XP_DELTA_CASES,
)


@pytest.mark.parametrize(
    ("case_id", "deltas", "domovoy_xp", "expected_xp"),
    XP_DELTA_CASES,
    ids=[case[0] for case in XP_DELTA_CASES],
)
def test_build_outcome_xp_delta_sums_domovoy_and_completed_challenges(
    case_id: str,
    deltas: list[ChallengeProgressDelta],
    domovoy_xp: int,
    expected_xp: int,
) -> None:
    result = outcome.build_outcome(
        RECEIPT,
        DECISION_COUNTED,
        domovoy_xp,
        DOMOVOY_STATE,
        deltas,
        RANK,
        None,
        APPROVE_DECISION,
        [],
    )
    assert result.xp_delta == expected_xp


@pytest.mark.parametrize(
    ("case_id", "unlocked", "expected_xp"),
    XP_DELTA_ACHIEVEMENTS_CASES,
    ids=[case[0] for case in XP_DELTA_ACHIEVEMENTS_CASES],
)
def test_build_outcome_xp_delta_adds_achievements_xp(
    case_id: str, unlocked: list[str], expected_xp: int
) -> None:
    result = outcome.build_outcome(
        RECEIPT, DECISION_COUNTED, 0, DOMOVOY_STATE, [], RANK, None, APPROVE_DECISION, unlocked
    )
    assert result.xp_delta == expected_xp
    assert result.achievements_unlocked == unlocked


def test_build_outcome_maps_fraud_decision_signals_verbatim() -> None:
    result = outcome.build_outcome(
        RECEIPT, DECISION_COUNTED, 0, DOMOVOY_STATE, [], RANK, None, BLOCK_DECISION, []
    )
    assert result.fraud.score == BLOCK_DECISION.score
    assert result.fraud.decision == BLOCK_DECISION.decision
    assert [s.model_dump() for s in result.fraud.signals] == [
        s.model_dump() for s in BLOCK_DECISION.signals
    ]


def test_build_outcome_savings_delta_delegates_to_savings_calc() -> None:
    result = outcome.build_outcome(
        RECEIPT, DECISION_COUNTED, 0, DOMOVOY_STATE, [], RANK, None, APPROVE_DECISION, []
    )
    expected = (
        (RECEIPT.regular_total - RECEIPT.paid_total) + RECEIPT.points_earned + RECEIPT.points_spent
    )
    assert result.savings_delta == expected


def test_build_outcome_passes_through_decision_rank_and_referral_status() -> None:
    decision = CountedDecision(counted=False, counted_reason="fraud_block")
    result = outcome.build_outcome(
        RECEIPT, decision, 0, DOMOVOY_STATE, [], RANK, "on_review", APPROVE_DECISION, []
    )
    assert result.receipt is RECEIPT
    assert result.counted is False
    assert result.counted_reason == "fraud_block"
    assert result.league_rank_before == RANK.rank_before
    assert result.league_rank_after == RANK.rank_after
    assert result.referral_status == "on_review"
    assert result.achievements_unlocked == []
