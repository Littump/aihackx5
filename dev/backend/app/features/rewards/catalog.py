from app.features.challenges.models import RewardKind
from app.features.rewards.models import RewardRule
from app.game_rules import (
    ACHIEVEMENT_STREAK_WEEKS,
    REFERRAL_REWARDS,
    REWARD_POINTS_MAX_WEEKLY,
    REWARD_POINTS_MIN,
    XP_ACHIEVEMENT,
    XP_CHALLENGE,
    XP_LEAGUE_PROMOTION,
    XP_LEAGUE_TOP3,
    XP_RECEIPT,
    XP_REFERRAL,
    XP_STREAK_4W,
)

EVENT_TITLES: dict[RewardKind, str] = {
    "receipt_xp": "Покупка засчитана",
    "challenge": "Цель недели выполнена",
    "streak": "Серия недель подряд",
    "league": "Итоги недели в лиге",
    "referral": "Приглашённый сосед",
    "achievement": "Новое достижение",
}


def earning_rules() -> list[RewardRule]:
    referrer_points = _referrer_points_range()
    return [
        RewardRule(
            code="receipt",
            title="Чек засчитан: покупка в Пятёрочке или Перекрёстке",
            xp=XP_RECEIPT,
            points_min=0,
            points_max=0,
        ),
        RewardRule(
            code="challenge",
            title="Цель недели выполнена",
            xp=XP_CHALLENGE,
            points_min=REWARD_POINTS_MIN,
            points_max=REWARD_POINTS_MAX_WEEKLY,
        ),
        RewardRule(
            code="streak",
            title=f"Серия из {ACHIEVEMENT_STREAK_WEEKS} недель с выполненной целью",
            xp=XP_STREAK_4W,
            points_min=0,
            points_max=0,
        ),
        RewardRule(
            code="league_promotion",
            title="Повышение в дивизионе лиги",
            xp=XP_LEAGUE_PROMOTION,
            points_min=0,
            points_max=0,
        ),
        RewardRule(
            code="league_top3",
            title="Топ-3 недели в лиге дома",
            xp=XP_LEAGUE_TOP3,
            points_min=0,
            points_max=0,
        ),
        RewardRule(
            code="referral",
            title="Приглашённый сосед дошёл до второй покупки",
            xp=XP_REFERRAL,
            points_min=referrer_points[0],
            points_max=referrer_points[1],
        ),
        RewardRule(
            code="achievement",
            title="Разблокировано достижение",
            xp=XP_ACHIEVEMENT,
            points_min=0,
            points_max=0,
        ),
    ]


def _referrer_points_range() -> tuple[int, int]:
    paid = [
        reward["referrer_reward_points"]
        for reward in REFERRAL_REWARDS.values()
        if reward["referrer_reward_points"] > 0
    ]
    if not paid:
        return (0, 0)
    return (min(paid), max(paid))
