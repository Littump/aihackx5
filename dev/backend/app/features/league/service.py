from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from psycopg import AsyncConnection

from app.core.clock import now, week_end, week_start
from app.features.league import database, rollover, scoring
from app.features.league import membership as league_membership
from app.features.league.models import (
    LeagueHouseView,
    LeagueMembership,
    LeagueMemberView,
    LeagueRankChange,
    LeagueRankedMemberRow,
    LeagueView,
    RolloverSummary,
    WeekTotals,
)
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptDetail, ReceiptWithItems
from app.features.savings import calc as savings_calc
from app.features.user_features import service as user_features_service
from app.features.users import service as users_service
from app.game_rules import DIVISION_NAMES, TIMEZONE, level_for_xp

TZ = ZoneInfo(TIMEZONE)


async def ensure_member(conn: AsyncConnection, user_id: int) -> LeagueMembership:
    await users_service.get_user(conn, user_id)
    week = week_start(now()).date()
    existing = await database.get_membership_for_week(conn, user_id=user_id, week_start=week)
    if existing is not None:
        return existing
    division = await _resolve_division(conn, user_id)
    store_id = await _resolve_store_id(conn, user_id)
    league = await league_membership.find_or_create_open_league(
        conn, store_id=store_id, division=division, week_start=week
    )
    await database.insert_member(conn, league_id=league.id, user_id=user_id)
    return LeagueMembership(
        league_id=league.id, division=league.division, store_id=league.store_id, score=0
    )


async def on_receipt(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> LeagueRankChange:
    if not receipt.counted:
        return LeagueRankChange(rank_before=None, rank_after=None)
    membership = await ensure_member(conn, user_id)
    rank_before = await database.get_member_rank(
        conn, league_id=membership.league_id, user_id=user_id
    )
    new_score = await _compute_score(conn, user_id)
    await database.update_member_score(
        conn, league_id=membership.league_id, user_id=user_id, score=new_score
    )
    rank_after = await database.get_member_rank(
        conn, league_id=membership.league_id, user_id=user_id
    )
    return LeagueRankChange(rank_before=rank_before, rank_after=rank_after)


async def get_league_view(conn: AsyncConnection, user_id: int) -> LeagueView:
    membership = await ensure_member(conn, user_id)
    league = await database.get_league_by_id(conn, league_id=membership.league_id)
    assert league is not None
    ranked = await database.list_ranked_members(conn, league_id=membership.league_id)
    size = len(ranked)
    my_row = next(row for row in ranked if row.user_id == user_id)
    members = await _members_view(conn, ranked=ranked, my_id=user_id)
    house = await _house_view(conn, store_id=league.store_id, week=league.week_start)
    return LeagueView(
        division=league.division,
        division_name=DIVISION_NAMES[league.division],
        week_start=league.week_start,
        week_end=week_end(now()).date(),
        size=size,
        my_rank=my_row.rank,
        my_score=my_row.score,
        my_zone=scoring.zone_for_rank(rank=my_row.rank, size=size, division=league.division),
        promotion_cutoff=scoring.promotion_cutoff(size),
        demotion_cutoff=scoring.demotion_cutoff(size),
        members=members,
        house=house,
    )


async def rollover_week(conn: AsyncConnection) -> RolloverSummary:
    return await rollover.rollover_week(conn)


async def _resolve_division(conn: AsyncConnection, user_id: int) -> int:
    division = await database.get_latest_division(conn, user_id=user_id)
    return division if division is not None else 1


async def _resolve_store_id(conn: AsyncConnection, user_id: int) -> int:
    features = await user_features_service.get(conn, user_id)
    if features.favourite_store_id is not None:
        return features.favourite_store_id
    default_store = await users_service.get_default_store(conn)
    return default_store.id


async def _compute_score(conn: AsyncConnection, user_id: int) -> int:
    from app.features.challenges import service as challenges_service
    from app.features.domovoy import service as domovoy_service

    week_from, week_to = week_start(now()), week_end(now())
    receipts = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=week_from, until=week_to
    )
    totals = _week_totals(receipts)
    completed = await challenges_service.count_completed_in_period(
        conn, user_id=user_id, start=week_from, end=week_to
    )
    domovoy_state = await domovoy_service.get_state(conn, user_id)
    return scoring.week_score(
        week_savings=totals.week_savings,
        week_regular_total=totals.week_regular_total,
        completed_challenges=completed,
        streak_weeks=domovoy_state.streak_weeks,
        counted_receipts=len(receipts),
    )


def _week_totals(receipts: list[ReceiptWithItems]) -> WeekTotals:
    savings = savings_calc.total_savings(receipts)
    regular_total = sum((r.regular_total for r in receipts), Decimal("0"))
    return WeekTotals(week_savings=savings, week_regular_total=regular_total)


async def _members_view(
    conn: AsyncConnection, *, ranked: list[LeagueRankedMemberRow], my_id: int
) -> list[LeagueMemberView]:
    user_ids = [row.user_id for row in ranked]
    users = await users_service.get_users_by_ids(conn, user_ids=user_ids)
    pseudonym_by_id = {u.id: u.pseudonym for u in users}
    levels = await _levels_by_id(conn, user_ids)
    return [
        LeagueMemberView(
            pseudonym=pseudonym_by_id[row.user_id],
            level=levels.get(row.user_id, level_for_xp(0)),
            score=row.score,
            rank=row.rank,
            is_me=row.user_id == my_id,
        )
        for row in ranked
    ]


async def _levels_by_id(conn: AsyncConnection, user_ids: list[int]) -> dict[int, int]:
    from app.features.domovoy import service as domovoy_service

    levels = await domovoy_service.get_levels(conn, user_ids=user_ids)
    return {row.user_id: row.level for row in levels}


async def _house_view(conn: AsyncConnection, *, store_id: int, week: date) -> LeagueHouseView:
    store = await users_service.get_store(conn, store_id)
    week_from = _week_moment(week)
    avg_rate = await _avg_savings_rate_for_store(conn, store_id=store_id, week_from=week_from)
    district_stores = await database.list_store_ids_with_leagues(conn, week_start=week)
    same_district = await _same_district_store_ids(
        conn, store_ids=[row.store_id for row in district_stores], district=store.district
    )
    rates: dict[int, Decimal] = {}
    for sid in same_district:
        rates[sid] = await _avg_savings_rate_for_store(conn, store_id=sid, week_from=week_from)
    ranked_stores = sorted(rates.items(), key=lambda pair: (-pair[1], pair[0]))
    rank = next(i for i, (sid, _) in enumerate(ranked_stores, start=1) if sid == store_id)
    return LeagueHouseView(
        store_name=store.name,
        avg_savings_rate=avg_rate,
        district_rank=rank,
        district_size=len(ranked_stores),
    )


async def _same_district_store_ids(
    conn: AsyncConnection, *, store_ids: list[int], district: str
) -> list[int]:
    stores = await users_service.get_stores_by_ids(conn, store_ids=store_ids)
    return [s.id for s in stores if s.district == district]


async def _avg_savings_rate_for_store(
    conn: AsyncConnection, *, store_id: int, week_from: datetime
) -> Decimal:
    week_to = week_end(week_from)
    members = await database.list_member_user_ids_for_store_week(
        conn, store_id=store_id, week_start=week_from.date()
    )
    if not members:
        return Decimal("0")
    rates: list[Decimal] = []
    for member in members:
        receipts = await receipts_service.list_counted_receipts_with_items(
            conn, user_id=member.user_id, since=week_from, until=week_to
        )
        totals = _week_totals(receipts)
        rates.append(scoring.savings_rate(totals.week_savings, totals.week_regular_total))
    return sum(rates, Decimal("0")) / len(rates)


def _week_moment(week: date) -> datetime:
    return datetime.combine(week, datetime.min.time(), tzinfo=TZ)
