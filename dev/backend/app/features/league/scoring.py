from decimal import ROUND_HALF_UP, Decimal

from app import game_rules
from app.features.league.models import LeagueZone


def savings_rate(week_savings: Decimal, week_regular_total: Decimal) -> Decimal:
    if week_regular_total <= 0:
        return Decimal("0")
    return week_savings / week_regular_total


def week_score(
    *,
    week_savings: Decimal,
    week_regular_total: Decimal,
    completed_challenges: int,
    streak_weeks: int,
    counted_receipts: int,
) -> int:
    rate_cap = Decimal(str(game_rules.LEAGUE_SCORE_SAVINGS_RATE_CAP))
    rate = savings_rate(week_savings, week_regular_total)
    capped_rate = min(max(rate, Decimal("0")), rate_cap)
    total = (
        Decimal(game_rules.LEAGUE_SCORE_SAVINGS_WEIGHT) * capped_rate
        + Decimal(game_rules.LEAGUE_SCORE_CHALLENGE_WEIGHT) * completed_challenges
        + Decimal(game_rules.LEAGUE_SCORE_STREAK_WEIGHT)
        * min(streak_weeks, game_rules.LEAGUE_SCORE_STREAK_CAP)
        + Decimal(game_rules.LEAGUE_SCORE_RECEIPTS_WEIGHT)
        * min(counted_receipts, game_rules.LEAGUE_SCORE_RECEIPTS_CAP)
    )
    return int(total.to_integral_value(rounding=ROUND_HALF_UP))


def promotion_cutoff(size: int) -> int:
    return min(game_rules.LEAGUE_PROMOTE_TOP, size)


def demotion_cutoff(size: int) -> int:
    raw = size - game_rules.LEAGUE_DEMOTE_BOTTOM + 1
    return max(raw, promotion_cutoff(size) + 1)


def zone_for_rank(*, rank: int, size: int, division: int) -> LeagueZone:
    can_promote = division < game_rules.LEAGUE_DIVISIONS_COUNT
    can_demote = division > 1
    if rank <= promotion_cutoff(size) and can_promote:
        return "promotion"
    if rank >= demotion_cutoff(size) and can_demote:
        return "demotion"
    return "safe"
