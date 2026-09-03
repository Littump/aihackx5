from datetime import datetime
from zoneinfo import ZoneInfo

from app import game_rules
from app.features.referrals.models import RefereeKind, ReferralInviteeRow, ReferralRow

TZ = ZoneInfo(game_rules.TIMEZONE)
REFERRAL_LINK_BASE = "https://x5.club/r/"


def rewards_for(kind: RefereeKind) -> dict[str, int]:
    return game_rules.REFERRAL_REWARDS[kind]


def referral_link(code: str) -> str:
    return f"{REFERRAL_LINK_BASE}{code}"


def rules_text() -> list[str]:
    return [
        f"Первая покупка соседа от {game_rules.REFERRAL_MIN_FIRST_PURCHASE} ₽ "
        "приносит ему баллы сразу.",
        f"Вторая покупка не раньше {game_rules.REFERRAL_SECOND_PURCHASE_MIN_DAYS} дней "
        "после первой приносит баллы и опыт вам.",
        f"Не больше {game_rules.REFERRAL_PAID_PER_MONTH} оплаченных приглашений в месяц и "
        f"{game_rules.REFERRAL_PAID_PER_YEAR} в год.",
    ]


def purchases_done(referral: ReferralRow) -> int:
    if referral.second_purchase_at is not None:
        return 2
    if referral.first_purchase_at is not None:
        return 1
    return 0


def to_invitee_view(referral: ReferralRow, index: int) -> ReferralInviteeRow:
    return ReferralInviteeRow(
        label=f"Сосед №{index}",
        referee_kind=referral.referee_kind,
        status=referral.status,
        purchases_done=purchases_done(referral),
        purchases_required=game_rules.REFERRAL_PURCHASES_REQUIRED,
        reward_points=referral.referrer_reward_points if referral.status == "rewarded" else 0,
        created_at=referral.created_at,
    )


def month_bounds(moment: datetime) -> tuple[datetime, datetime]:
    local = moment.astimezone(TZ)
    start = datetime(local.year, local.month, 1, tzinfo=TZ)
    return start, _add_month(start)


def year_bounds(moment: datetime) -> tuple[datetime, datetime]:
    local = moment.astimezone(TZ)
    start = datetime(local.year, 1, 1, tzinfo=TZ)
    return start, start.replace(year=local.year + 1)


def _add_month(moment: datetime) -> datetime:
    if moment.month == 12:
        return moment.replace(year=moment.year + 1, month=1)
    return moment.replace(month=moment.month + 1)
