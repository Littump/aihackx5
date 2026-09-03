from datetime import date
from typing import Literal

from app.core.models import AppModel


class LeagueMember(AppModel):
    pseudonym: str
    level: int
    score: int
    rank: int
    is_me: bool


class LeagueHouse(AppModel):
    store_name: str
    avg_savings_rate: float
    district_rank: int
    district_size: int


class RolloverResult(AppModel):
    leagues_closed: int
    users_promoted: int
    users_demoted: int
    week_start: date


class LeagueResponse(AppModel):
    division: int
    division_name: str
    week_start: date
    week_end: date
    size: int
    my_rank: int
    my_score: int
    my_zone: Literal["promotion", "safe", "demotion"]
    promotion_cutoff: int
    demotion_cutoff: int
    members: list[LeagueMember]
    house: LeagueHouse
