from datetime import datetime
from typing import Literal

from app.core.models import AppModel

RefereeKindDto = Literal["new", "dormant", "active"]
ReferralStatusDto = Literal[
    "pending", "first_purchase", "qualified", "on_review", "rewarded", "blocked"
]


class ReferralInvitee(AppModel):
    label: str
    referee_kind: RefereeKindDto
    status: ReferralStatusDto
    purchases_done: int
    purchases_required: int
    reward_points: int
    created_at: datetime


class ReferralResponse(AppModel):
    code: str
    link: str
    rules: list[str]
    referrer_reward_points: int
    referee_reward_points_new: int
    referee_reward_points_dormant: int
    invitees: list[ReferralInvitee]
    paid_this_month: int
    paid_limit_month: int


class RedeemReferralInput(AppModel):
    code: str
    device_fingerprint: str | None = None
    pseudonym: str | None = None


class RedeemReferralResponse(AppModel):
    referee_user_id: int
    referrer_user_id: int
    referee_kind: RefereeKindDto
    status: ReferralStatusDto
