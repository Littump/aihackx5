from decimal import Decimal

from app.features.achievements.models import AchievementContext
from app.game_rules import ACHIEVEMENT_STREAK_WEEKS, SAVER_1000_THRESHOLD_RUB


def _ctx(**overrides: object) -> AchievementContext:
    base: dict[str, object] = {
        "is_first_receipt": False,
        "streak_weeks": 0,
        "savings_month": Decimal("0"),
        "chains_last_30d": [],
    }
    base.update(overrides)
    return AchievementContext.model_validate(base)


EVALUATE_CASES: list[tuple[str, AchievementContext, list[str]]] = [
    ("nothing_matches", _ctx(), []),
    ("first_receipt", _ctx(is_first_receipt=True), ["first_receipt"]),
    (
        "streak_below_threshold_does_not_unlock",
        _ctx(streak_weeks=ACHIEVEMENT_STREAK_WEEKS - 1),
        [],
    ),
    ("streak_at_threshold_unlocks", _ctx(streak_weeks=ACHIEVEMENT_STREAK_WEEKS), ["streak_4"]),
    (
        "savings_below_threshold_does_not_unlock",
        _ctx(savings_month=Decimal(SAVER_1000_THRESHOLD_RUB - 1)),
        [],
    ),
    (
        "savings_at_threshold_unlocks",
        _ctx(savings_month=Decimal(SAVER_1000_THRESHOLD_RUB)),
        ["saver_1000"],
    ),
    (
        "single_chain_does_not_unlock_explorer",
        _ctx(chains_last_30d=["pyaterochka"]),
        [],
    ),
    (
        "both_chains_unlock_explorer",
        _ctx(chains_last_30d=["pyaterochka", "perekrestok"]),
        ["explorer"],
    ),
    (
        "several_conditions_unlock_together",
        _ctx(is_first_receipt=True, streak_weeks=ACHIEVEMENT_STREAK_WEEKS),
        ["first_receipt", "streak_4"],
    ),
]
