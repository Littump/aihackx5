from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

RefereeKind = Literal["new", "dormant", "active"]
ReferralStatus = Literal[
    "pending", "first_purchase", "qualified", "on_review", "rewarded", "blocked"
]


class ReferralRow(AppModel):
    id: int
    referrer_user_id: int
    referee_user_id: int
    referee_kind: RefereeKind
    status: ReferralStatus
    first_purchase_at: datetime | None
    second_purchase_at: datetime | None
    fraud_score: Decimal | None
    fraud_reasons: list[str]
    referrer_reward_points: int
    referee_reward_points: int
    created_at: datetime
    decided_at: datetime | None


class ReferralProgressDelta(AppModel):
    referral_id: int
    status: ReferralStatus


class ReferralInviteeRow(AppModel):
    label: str
    referee_kind: RefereeKind
    status: ReferralStatus
    purchases_done: int
    purchases_required: int
    reward_points: int
    created_at: datetime


class ReferralPageView(AppModel):
    code: str
    link: str
    rules: list[str]
    referrer_reward_points: int
    referee_reward_points_new: int
    referee_reward_points_dormant: int
    invitees: list[ReferralInviteeRow]
    paid_this_month: int
    paid_limit_month: int


class RedeemReferralResult(AppModel):
    referee_user_id: int
    referrer_user_id: int
    referee_kind: RefereeKind
    status: ReferralStatus
