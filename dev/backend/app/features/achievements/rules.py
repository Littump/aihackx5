from app.features.achievements.models import AchievementContext
from app.game_rules import ACHIEVEMENT_STREAK_WEEKS, SAVER_1000_THRESHOLD_RUB

EXPLORER_REQUIRED_CHAINS = frozenset({"pyaterochka", "perekrestok"})


def evaluate(ctx: AchievementContext) -> list[str]:
    checks = (
        (ctx.is_first_receipt, "first_receipt"),
        (ctx.streak_weeks >= ACHIEVEMENT_STREAK_WEEKS, "streak_4"),
        (ctx.savings_month >= SAVER_1000_THRESHOLD_RUB, "saver_1000"),
        (_is_explorer(ctx.chains_last_30d), "explorer"),
    )
    return [code for matched, code in checks if matched]


def _is_explorer(chains: list[str]) -> bool:
    return EXPLORER_REQUIRED_CHAINS.issubset(set(chains))
