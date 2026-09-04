from typing import Literal

from app.core.models import AppModel
from app.features.challenges.dto import ChallengeDetail
from app.features.receipts.dto import DomovoyState
from app.features.savings.dto import SavingsSummary


class UserSummary(AppModel):
    id: int
    pseudonym: str
    segment: Literal["regular_mid", "light", "heavy", "dormant"]
    level: int


class UserListResponse(AppModel):
    items: list[UserSummary]


class LeagueTeaser(AppModel):
    division: int
    rank: int
    size: int
    zone: Literal["promotion", "safe", "demotion"]


class ReferralTeaser(AppModel):
    code: str
    invited_count: int
    rewarded_count: int


class RecommendedMechanic(AppModel):
    mechanic: Literal["challenge", "league", "referral"]
    reason: str


class HomeResponse(AppModel):
    user: UserSummary
    domovoy: DomovoyState
    savings: SavingsSummary
    points_balance: int
    insight: str
    hero_challenge: ChallengeDetail | None
    league: LeagueTeaser | None
    referral: ReferralTeaser
    recommended_mechanic: RecommendedMechanic
