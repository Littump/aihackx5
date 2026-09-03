from psycopg import AsyncConnection

from app.features.antifraud.models import FraudDecision
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy.models import DomovoyDelta, DomovoyStateRow
from app.features.league.models import LeagueRankChange
from app.features.receipts.models import DomovoyStateStub, ReceiptDetail, ReceiptRow
from app.game_rules import level_for_xp, xp_to_next_level


async def run_antifraud_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> FraudDecision:
    # отложенный импорт разрывает цикл: antifraud.service импортирует нас
    from app.features.antifraud import service as antifraud_service

    return await antifraud_service.check_receipt(conn, user_id, receipt)


async def run_domovoy_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> DomovoyDelta:
    # отложенный импорт разрывает цикл: domovoy.service импортирует нас
    from app.features.domovoy import service as domovoy_service

    return await domovoy_service.on_receipt(conn, user_id, receipt)


async def run_challenges_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> list[ChallengeProgressDelta]:
    # отложенный импорт: challenges тянет user_features, который тянет нас
    from app.features.challenges import service as challenges_service

    return await challenges_service.on_receipt(conn, user_id, receipt)


async def run_league_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> LeagueRankChange:
    # отложенный импорт разрывает цикл: league.service импортирует нас
    from app.features.league import service as league_service

    return await league_service.on_receipt(conn, user_id, receipt)


async def run_referral_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> str | None:
    # отложенный импорт разрывает цикл: referrals.service тянет соседей
    from app.features.referrals import service as referrals_service

    delta = await referrals_service.on_receipt(conn, user_id, receipt)
    return delta.status if delta is not None else None


async def run_achievements_step(
    conn: AsyncConnection,
    user_id: int,
    *,
    receipt: ReceiptDetail,
    challenge_deltas: list[ChallengeProgressDelta],
    referral_status: str | None,
) -> list[str]:
    # отложенный импорт разрывает цикл: achievements.service тянет соседей
    from app.features.achievements import service as achievements_service

    return await achievements_service.on_receipt(
        conn,
        user_id,
        receipt=receipt,
        challenge_deltas=challenge_deltas,
        referral_status=referral_status,
    )


async def final_domovoy_state(conn: AsyncConnection, user_id: int) -> DomovoyStateStub:
    # отложенный импорт разрывает цикл: domovoy.service импортирует нас
    from app.features.domovoy import service as domovoy_service

    state: DomovoyStateRow = await domovoy_service.get_state(conn, user_id)
    return DomovoyStateStub(
        xp=state.xp,
        level=level_for_xp(state.xp),
        xp_to_next_level=xp_to_next_level(state.xp),
        mood=state.mood,
        mood_reason=state.mood_reason,
        streak_weeks=state.streak_weeks,
        items=state.items,
    )
