from datetime import date

from psycopg import AsyncConnection

from app.core.clock import now, week_start
from app.features.league import database, membership, scoring
from app.features.league.models import (
    LeagueRankedMemberRow,
    LeagueRow,
    MemberRolloverOutcome,
    RolloverSummary,
)
from app.game_rules import LEAGUE_TOP3_RANK, XP_LEAGUE_PROMOTION, XP_LEAGUE_TOP3


async def rollover_week(conn: AsyncConnection) -> RolloverSummary:
    week = week_start(now()).date()
    stale_leagues = await database.list_open_leagues_before(conn, week_start=week)
    users_promoted = 0
    users_demoted = 0
    for league in stale_leagues:
        ranked = await database.list_ranked_members(conn, league_id=league.id)
        for row in ranked:
            outcome = await _rollover_member(
                conn, league=league, row=row, size=len(ranked), new_week=week
            )
            users_promoted += int(outcome.promoted)
            users_demoted += int(outcome.demoted)
        await database.close_league(conn, league_id=league.id)
    return RolloverSummary(
        leagues_closed=len(stale_leagues),
        users_promoted=users_promoted,
        users_demoted=users_demoted,
        week_start=week,
    )


async def _rollover_member(
    conn: AsyncConnection,
    *,
    league: LeagueRow,
    row: LeagueRankedMemberRow,
    size: int,
    new_week: date,
) -> MemberRolloverOutcome:
    from app.features.achievements import service as achievements_service
    from app.features.domovoy import service as domovoy_service

    zone = scoring.zone_for_rank(rank=row.rank, size=size, division=league.division)
    if zone == "promotion":
        await domovoy_service.add_xp(
            conn,
            row.user_id,
            XP_LEAGUE_PROMOTION,
            kind="league",
            ref_type="league",
            ref_id=league.id,
            points_delta=0,
        )
    if row.rank <= LEAGUE_TOP3_RANK:
        await domovoy_service.add_xp(
            conn,
            row.user_id,
            XP_LEAGUE_TOP3,
            kind="league",
            ref_type="league",
            ref_id=league.id,
            points_delta=0,
        )
        await achievements_service.unlock(conn, row.user_id, "league_top3")
    new_division = scoring.next_division(division=league.division, zone=zone)
    target = await membership.find_or_create_open_league(
        conn, store_id=league.store_id, division=new_division, week_start=new_week
    )
    await _place_member_authoritatively(
        conn, target_league_id=target.id, user_id=row.user_id, new_week=new_week
    )
    return MemberRolloverOutcome(promoted=zone == "promotion", demoted=zone == "demotion")


async def _place_member_authoritatively(
    conn: AsyncConnection, *, target_league_id: int, user_id: int, new_week: date
) -> None:
    existing = await database.get_membership_for_week(conn, user_id=user_id, week_start=new_week)
    if existing is not None and existing.league_id == target_league_id:
        return
    carried_score = 0
    if existing is not None:
        carried_score = existing.score
        await database.delete_member(conn, league_id=existing.league_id, user_id=user_id)
    await database.insert_member(
        conn, league_id=target_league_id, user_id=user_id, score=carried_score
    )
