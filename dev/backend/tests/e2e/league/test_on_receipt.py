from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection

from app.features.challenges import database as challenges_db
from app.features.league import database as league_db
from app.features.league import service as league_service
from app.features.receipts.models import ReceiptDetail, ReceiptRow
from tests.e2e.league.data import DISCOUNT_ITEM, NO_SAVINGS_ITEM, NOW
from tests.factories import (
    make_challenge,
    make_domovoy_state,
    make_receipt,
    make_store,
    make_user,
    make_user_features,
)


def _trigger(receipt: ReceiptRow, *, counted: bool = True) -> ReceiptDetail:
    return ReceiptDetail(
        id=receipt.id,
        store_id=receipt.store_id,
        store_name="Дом",
        purchased_at=receipt.purchased_at,
        regular_total=receipt.regular_total,
        paid_total=receipt.paid_total,
        discount_total=receipt.discount_total,
        points_earned=0,
        points_spent=0,
        counted=counted,
        is_returned=False,
        items=[],
    )


async def test_on_receipt_score_matches_domain_rules_example(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user = await make_user(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)
    await make_domovoy_state(conn, user.id, streak_weeks=3)
    challenge = await make_challenge(conn, user.id, status="active", target=Decimal("1"))
    await challenges_db.update_progress(
        conn,
        challenge_id=challenge.id,
        progress=Decimal("1"),
        status="completed",
        completed_at=NOW,
    )
    receipts = [
        await make_receipt(conn, user.id, store_id=store.id, purchased_at=NOW, items=DISCOUNT_ITEM)
        for _ in range(4)
    ]

    change = await league_service.on_receipt(conn, user.id, _trigger(receipts[-1]))

    assert change.rank_before == 1
    assert change.rank_after == 1
    membership = await league_service.ensure_member(conn, user.id)
    ranked = await league_db.list_ranked_members(conn, league_id=membership.league_id)
    assert ranked[0].score == 124


async def test_on_receipt_updates_rank_when_challenger_overtakes_leader(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    leader = await make_user(conn)
    await make_user_features(conn, leader.id, favourite_store_id=store.id)
    leader_membership = await league_service.ensure_member(conn, leader.id)
    await league_db.update_member_score(
        conn, league_id=leader_membership.league_id, user_id=leader.id, score=50
    )

    challenger = await make_user(conn)
    await make_user_features(conn, challenger.id, favourite_store_id=store.id)
    await make_domovoy_state(conn, challenger.id, streak_weeks=5)
    receipt = await make_receipt(
        conn, challenger.id, store_id=store.id, purchased_at=NOW, items=NO_SAVINGS_ITEM
    )

    change = await league_service.on_receipt(conn, challenger.id, _trigger(receipt))

    assert change.rank_before == 2
    assert change.rank_after == 1


async def test_on_receipt_skips_not_counted_receipt(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = await make_receipt(conn, user.id, purchased_at=NOW, counted=False)

    change = await league_service.on_receipt(conn, user.id, _trigger(receipt, counted=False))

    assert change.rank_before is None
    assert change.rank_after is None


async def test_on_receipt_excludes_returned_receipt_from_score(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user = await make_user(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)
    returned = await make_receipt(
        conn,
        user.id,
        store_id=store.id,
        purchased_at=NOW,
        items=DISCOUNT_ITEM,
        is_returned=True,
    )

    change = await league_service.on_receipt(conn, user.id, _trigger(returned))

    assert change.rank_before == 1
    assert change.rank_after == 1
    membership = await league_service.ensure_member(conn, user.id)
    ranked = await league_db.list_ranked_members(conn, league_id=membership.league_id)
    assert ranked[0].score == 0
