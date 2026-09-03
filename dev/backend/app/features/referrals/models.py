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
