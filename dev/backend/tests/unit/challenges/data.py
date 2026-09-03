from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from app.features.challenges.models import (
    ChallengeDraft,
    ChallengeEconomics,
    ChallengeRow,
    RationaleFeatures,
)
from app.features.receipts.models import ReceiptItemRow, ReceiptWithItems
from app.features.user_features.models import CategoryAffinity, UserFeaturesRow
from app.features.users.models import UserRow

COMPUTED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
DEFAULT_WINDOW_WEEKS = 10
FREQUENCY_DISABLED = Decimal("6")
RECEIPT_PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def make_features(
    *,
    frequency_per_week: Decimal = Decimal("0"),
    recency_days: int | None = 999,
    avg_basket: Decimal = Decimal("0"),
    category_affinity: dict[str, CategoryAffinity] | None = None,
    window_weeks: int = DEFAULT_WINDOW_WEEKS,
) -> UserFeaturesRow:
    return UserFeaturesRow(
        user_id=1,
        computed_at=COMPUTED_AT,
        window_weeks=window_weeks,
        frequency_per_week=frequency_per_week,
        recency_days=recency_days,
        avg_basket=avg_basket,
        promo_sensitivity=Decimal("0"),
        cadence_days=None,
        category_affinity=category_affinity or {},
        weekday_pattern=[0.0] * 7,
        realized_savings_30d=Decimal("0"),
        favourite_store_id=None,
        cross_chain_share=Decimal("0"),
    )


NO_HISTORY_FEATURES = make_features()

FREQUENCY_HEADROOM_CASES: list[tuple[Decimal, bool]] = [
    (Decimal("5.9"), True),
    (Decimal("5.99"), True),
    (Decimal("6"), False),
    (Decimal("6.1"), False),
]

RECENCY_BOUNDARY_CASES: list[tuple[int, bool]] = [
    (21, True),
    (22, False),
]

CATEGORY_AFFINITY_CASES: list[tuple[str, float, int, bool]] = [
    ("dairy", 0.10, 3, True),
    ("dairy", 0.099, 3, False),
    ("dairy", 0.10, 2, False),
    ("alcohol", 0.5, 10, False),
    ("alcohol", 0.10, 3, False),
]

TARGET_CASES: list[tuple[Decimal, Decimal]] = [
    (Decimal("2"), Decimal("3")),
    (Decimal("5"), Decimal("6")),
]

BASELINE_FLOOR_CASES: list[tuple[Decimal, Decimal]] = [
    (Decimal("0"), Decimal("1")),
    (Decimal("0.4"), Decimal("1")),
]

ECONOMICS_CASES: list[tuple[Decimal, Decimal, Decimal, Decimal, Decimal, int]] = [
    (Decimal("2"), Decimal("3"), Decimal("600"), Decimal("90"), Decimal("36"), 30),
    (Decimal("1.5"), Decimal("3"), Decimal("555"), Decimal("124.875"), Decimal("49.95"), 40),
    (Decimal("2"), Decimal("3"), Decimal("150"), Decimal("22.5"), Decimal("9"), 0),
]


def make_draft(
    *,
    type: Literal["frequency", "category"] = "frequency",
    category: str | None = None,
    baseline: Decimal = Decimal("2"),
    target: Decimal = Decimal("3"),
    priority: float = 1.0,
    frequency_per_week: float | None = None,
    share: float | None = None,
    visits: int | None = None,
) -> ChallengeDraft:
    return ChallengeDraft(
        type=type,
        category=category,
        baseline=baseline,
        target=target,
        priority=priority,
        rationale_features=RationaleFeatures(
            frequency_per_week=frequency_per_week, share=share, visits=visits
        ),
    )


def make_challenge_row(
    *,
    id: int = 1,
    user_id: int = 1,
    type: Literal["frequency", "category"] = "frequency",
    category: str | None = None,
    status: Literal["active", "completed", "failed", "expired"] = "active",
    is_hero: bool = True,
    baseline: Decimal = Decimal("2"),
    target: Decimal = Decimal("3"),
    progress: Decimal = Decimal("0"),
) -> ChallengeRow:
    return ChallengeRow(
        id=id,
        user_id=user_id,
        type=type,
        category=category,
        status=status,
        is_hero=is_hero,
        baseline=baseline,
        target=target,
        progress=progress,
        period_start=COMPUTED_AT,
        period_end=COMPUTED_AT,
        reward_xp=50,
        reward_points=30,
        economics=ChallengeEconomics(
            avg_basket=0.0,
            expected_incremental_purchases=0.0,
            expected_incremental_margin=0.0,
            max_reward_rub=0.0,
            contribution_margin=0.0,
            reward_share_max=0.0,
        ),
        rationale_features={},
        copy_title="Заголовок",
        copy_body="Текст",
        copy_explanation="Почему",
        copy_source="template",
        created_at=COMPUTED_AT,
        completed_at=None,
    )


def make_receipt_with_items(
    *,
    receipt_id: int = 1,
    purchased_at: datetime = RECEIPT_PURCHASED_AT,
    categories: list[str] | None = None,
) -> ReceiptWithItems:
    picked = categories if categories is not None else ["dairy"]
    items = [
        ReceiptItemRow(
            id=i,
            receipt_id=receipt_id,
            product_name=category,
            category=category,
            qty=Decimal("1"),
            regular_price=Decimal("100.00"),
            paid_price=Decimal("100.00"),
            is_promo=False,
        )
        for i, category in enumerate(picked, start=1)
    ]
    return ReceiptWithItems(
        id=receipt_id,
        store_id=1,
        purchased_at=purchased_at,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("100.00"),
        points_earned=0,
        points_spent=0,
        items=items,
    )


def make_user_row(*, user_id: int = 1) -> UserRow:
    return UserRow(
        id=user_id,
        pseudonym="Домовой",
        segment="regular_mid",
        favourite_store_id=None,
        referral_code=f"CODE{user_id}",
        referred_by_user_id=None,
        device_fingerprint=None,
        social_propensity=Decimal("0"),
        created_at=COMPUTED_AT,
    )
