from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

LeagueStatus = Literal["open", "closed"]
LeagueZone = Literal["promotion", "safe", "demotion"]


class LeagueRow(AppModel):
    id: int
    store_id: int
    division: int
    week_start: date
    status: LeagueStatus


class LeagueMemberRow(AppModel):
    league_id: int
    user_id: int
    score: int
    joined_at: datetime


class LeagueMembership(AppModel):
    league_id: int
    division: int
    store_id: int


class LeagueRankChange(AppModel):
    rank_before: int | None
    rank_after: int | None


class WeekTotals(AppModel):
    week_savings: Decimal
    week_regular_total: Decimal


class LeagueRankedMemberRow(AppModel):
    user_id: int
    score: int
    rank: int


class LeagueMemberUserRow(AppModel):
    user_id: int


class LeagueStoreWeekRow(AppModel):
    store_id: int


class LeagueMemberView(AppModel):
    pseudonym: str
    level: int
    score: int
    rank: int
    is_me: bool


class LeagueHouseView(AppModel):
    store_name: str
    avg_savings_rate: Decimal
    district_rank: int
    district_size: int


class LeagueView(AppModel):
    division: int
    division_name: str
    week_start: date
    week_end: date
    size: int
    my_rank: int
    my_score: int
    my_zone: LeagueZone
    promotion_cutoff: int
    demotion_cutoff: int
    members: list[LeagueMemberView]
    house: LeagueHouseView
