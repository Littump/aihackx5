from datetime import UTC, datetime
from decimal import Decimal

from app.features.antifraud.models import FraudDecision, FraudSignal
from app.features.challenges.models import ChallengeProgressDelta
from app.features.league.models import LeagueRankChange
from app.features.receipts.models import CountedDecision, DomovoyStateStub, ReceiptDetail

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)

RECEIPT = ReceiptDetail(
    id=1,
    store_id=1,
    store_name="Пятёрочка",
    purchased_at=PURCHASED_AT,
    regular_total=Decimal("200.00"),
    paid_total=Decimal("150.00"),
    discount_total=Decimal("50.00"),
    points_earned=10,
    points_spent=5,
    counted=True,
    is_returned=False,
    items=[],
)
DECISION_COUNTED = CountedDecision(counted=True, counted_reason=None)
RANK = LeagueRankChange(rank_before=5, rank_after=4)
DOMOVOY_STATE = DomovoyStateStub(
    xp=110, level=2, xp_to_next_level=190, mood="cozy", mood_reason="", streak_weeks=0, items=[]
)
APPROVE_DECISION = FraudDecision(score=0.0, decision="approve", signals=[])
BLOCK_DECISION = FraudDecision(
    score=0.9,
    decision="block",
    signals=[
        FraudSignal(
            code="same_pos_share",
            weight=0.30,
            strong=True,
            detail="100% чеков через один pos_id (5 из 5)",
        ),
        FraudSignal(
            code="basket_monotony",
            weight=0.15,
            strong=False,
            detail="5 чека подряд с одинаковым составом и суммой",
        ),
    ],
)


def _delta(
    challenge_id: int, *, completed: bool, reward_xp: int, reward_points: int = 0
) -> ChallengeProgressDelta:
    return ChallengeProgressDelta(
        challenge_id=challenge_id,
        progress_before=Decimal("0"),
        progress_after=Decimal("1"),
        target=Decimal("2"),
        completed=completed,
        reward_points=reward_points,
        reward_xp=reward_xp,
    )


XP_DELTA_CASES: list[tuple[str, list[ChallengeProgressDelta], int, int]] = [
    ("no_challenges", [], 10, 10),
    ("one_completed_adds_reward_xp", [_delta(1, completed=True, reward_xp=50)], 10, 60),
    (
        "incomplete_challenge_does_not_add_xp",
        [_delta(1, completed=True, reward_xp=50), _delta(2, completed=False, reward_xp=0)],
        10,
        60,
    ),
    (
        "two_completed_challenges_sum",
        [_delta(1, completed=True, reward_xp=50), _delta(2, completed=True, reward_xp=30)],
        5,
        85,
    ),
    ("domovoy_delta_zero_and_no_challenges", [], 0, 0),
]
