from app.features.challenges.models import ChallengeProgressDelta
from app.features.league.models import LeagueRankChange
from app.features.receipts.models import (
    ChallengeProgressDeltaStub,
    CountedDecision,
    DomovoyStateStub,
    FraudDecisionStub,
    ReceiptDetail,
    ReceiptProcessingOutcome,
)
from app.features.savings import calc as savings_calc


def build_outcome(
    receipt: ReceiptDetail,
    decision: CountedDecision,
    domovoy_xp_delta: int,
    domovoy_state: DomovoyStateStub,
    challenge_deltas: list[ChallengeProgressDelta],
    league_rank_change: LeagueRankChange,
) -> ReceiptProcessingOutcome:
    xp_delta = domovoy_xp_delta + _completed_challenges_xp(challenge_deltas)
    return ReceiptProcessingOutcome(
        receipt=receipt,
        counted=decision.counted,
        counted_reason=decision.counted_reason,
        xp_delta=xp_delta,
        domovoy=domovoy_state,
        savings_delta=savings_calc.receipt_savings(receipt),
        challenges=_map_challenge_deltas(challenge_deltas),
        league_rank_before=league_rank_change.rank_before,
        league_rank_after=league_rank_change.rank_after,
        referral_status=None,
        fraud=_stub_fraud_decision(),
        achievements_unlocked=[],
    )


def _completed_challenges_xp(deltas: list[ChallengeProgressDelta]) -> int:
    return sum(delta.reward_xp for delta in deltas if delta.completed)


def _map_challenge_deltas(
    deltas: list[ChallengeProgressDelta],
) -> list[ChallengeProgressDeltaStub]:
    return [ChallengeProgressDeltaStub.model_validate(delta) for delta in deltas]


def _stub_fraud_decision() -> FraudDecisionStub:
    return FraudDecisionStub(score=0.0, decision="approve", signals=[])
