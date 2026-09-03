from collections.abc import Sequence
from datetime import datetime, timedelta

from psycopg import AsyncConnection

from app.core.clock import day_start
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy.models import DomovoyDelta, DomovoyStateRow
from app.features.receipts import database, outcome
from app.features.receipts.models import (
    CountedDecision,
    DomovoyStateStub,
    ReceiptDetail,
    ReceiptItemDraft,
    ReceiptItemInputLike,
    ReceiptItemRow,
    ReceiptProcessingOutcome,
    ReceiptRow,
    ReceiptTotals,
    ReceiptWithItems,
    SimulateScenario,
)
from app.features.receipts.totals import compute_totals
from app.features.users import service as users_service
from app.game_rules import (
    RECEIPT_DEDUP_WINDOW_MIN,
    RECEIPTS_PER_DAY_MAX,
    level_for_xp,
    xp_to_next_level,
)


async def process_receipt(
    conn: AsyncConnection,
    *,
    user_id: int,
    store_id: int,
    purchased_at: datetime,
    points_earned: int,
    points_spent: int,
    pos_id: str | None,
    items: Sequence[ReceiptItemInputLike],
) -> ReceiptProcessingOutcome:
    await users_service.get_user(conn, user_id)
    store = await users_service.get_store(conn, store_id)
    drafts = _draft_items(items)
    totals = compute_totals(drafts)
    decision = await _decide_counted(
        conn, user_id=user_id, store_id=store_id, purchased_at=purchased_at
    )
    receipt_row = await _insert_receipt(
        conn,
        user_id=user_id,
        store_id=store_id,
        purchased_at=purchased_at,
        totals=totals,
        points_earned=points_earned,
        points_spent=points_spent,
        pos_id=pos_id,
        counted=decision.counted,
    )
    item_rows = await _insert_items(conn, receipt_id=receipt_row.id, items=drafts)
    await _recompute_user_features(conn, user_id)
    domovoy_delta = await _run_domovoy_step(conn, user_id, receipt_row)
    receipt_detail = _to_receipt_detail(receipt_row, store_name=store.name, items=item_rows)
    challenge_deltas = await _run_challenges_step(conn, user_id, receipt_detail)
    domovoy_state = await _final_domovoy_state(conn, user_id)
    return outcome.build_outcome(
        receipt_detail, decision, domovoy_delta.xp_delta, domovoy_state, challenge_deltas
    )


async def simulate_receipt(
    conn: AsyncConnection,
    *,
    user_id: int,
    scenario: SimulateScenario,
    store_id: int | None,
) -> ReceiptProcessingOutcome:
    # отложенный импорт разрывает цикл: simulate.py зовёт process_receipt
    from app.features.receipts import simulate

    return await simulate.simulate_receipt(
        conn, user_id=user_id, scenario=scenario, store_id=store_id
    )


async def list_receipts(conn: AsyncConnection, *, user_id: int, limit: int) -> list[ReceiptDetail]:
    await users_service.get_user(conn, user_id)
    rows = await database.list_receipts_for_user(conn, user_id=user_id, limit=limit)
    if not rows:
        return []
    item_rows = await database.list_receipt_items_for_receipts(
        conn, receipt_ids=[row.id for row in rows]
    )
    items_by_receipt: dict[int, list[ReceiptItemRow]] = {}
    for item in item_rows:
        items_by_receipt.setdefault(item.receipt_id, []).append(item)
    store_names: dict[int, str] = {}
    for row in rows:
        if row.store_id not in store_names:
            store = await users_service.get_store(conn, row.store_id)
            store_names[row.store_id] = store.name
    return [
        _to_receipt_detail(
            row, store_name=store_names[row.store_id], items=items_by_receipt.get(row.id, [])
        )
        for row in rows
    ]


async def list_counted_receipts_with_items(
    conn: AsyncConnection, *, user_id: int, since: datetime, until: datetime | None = None
) -> list[ReceiptWithItems]:
    rows = await database.list_counted_receipts_since(
        conn, user_id=user_id, since=since, until=until
    )
    if not rows:
        return []
    item_rows = await database.list_receipt_items_for_receipts(
        conn, receipt_ids=[row.id for row in rows]
    )
    items_by_receipt: dict[int, list[ReceiptItemRow]] = {}
    for item in item_rows:
        items_by_receipt.setdefault(item.receipt_id, []).append(item)
    return [
        ReceiptWithItems(
            id=row.id,
            store_id=row.store_id,
            purchased_at=row.purchased_at,
            regular_total=row.regular_total,
            paid_total=row.paid_total,
            points_earned=row.points_earned,
            points_spent=row.points_spent,
            items=items_by_receipt.get(row.id, []),
        )
        for row in rows
    ]


async def _recompute_user_features(conn: AsyncConnection, user_id: int) -> None:
    # отложенный импорт разрывает цикл: user_features.service импортирует нас
    from app.features.user_features import service as user_features_service

    await user_features_service.recompute(conn, user_id)


def _draft_items(items: Sequence[ReceiptItemInputLike]) -> list[ReceiptItemDraft]:
    return [ReceiptItemDraft.model_validate(item) for item in items]


async def _run_domovoy_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> DomovoyDelta:
    # отложенный импорт разрывает цикл: domovoy.service импортирует нас
    from app.features.domovoy import service as domovoy_service

    return await domovoy_service.on_receipt(conn, user_id, receipt)


async def _run_challenges_step(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> list[ChallengeProgressDelta]:
    # отложенный импорт: challenges тянет user_features, который тянет нас
    from app.features.challenges import service as challenges_service

    return await challenges_service.on_receipt(conn, user_id, receipt)


async def _final_domovoy_state(conn: AsyncConnection, user_id: int) -> DomovoyStateStub:
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


async def _decide_counted(
    conn: AsyncConnection, *, user_id: int, store_id: int, purchased_at: datetime
) -> CountedDecision:
    dedup = await database.exists_counted_receipt_in_store_within_window(
        conn,
        user_id=user_id,
        store_id=store_id,
        purchased_at=purchased_at,
        window_minutes=RECEIPT_DEDUP_WINDOW_MIN,
    )
    if dedup:
        return CountedDecision(counted=False, counted_reason="dedup_window")
    start = day_start(purchased_at)
    today_count = await database.count_counted_receipts_in_range(
        conn, user_id=user_id, start=start, end=start + timedelta(days=1)
    )
    if today_count >= RECEIPTS_PER_DAY_MAX:
        return CountedDecision(counted=False, counted_reason="daily_limit")
    return CountedDecision(counted=True, counted_reason=None)


async def _insert_receipt(
    conn: AsyncConnection,
    *,
    user_id: int,
    store_id: int,
    purchased_at: datetime,
    totals: ReceiptTotals,
    points_earned: int,
    points_spent: int,
    pos_id: str | None,
    counted: bool,
) -> ReceiptRow:
    return await database.insert_receipt(
        conn,
        {
            "user_id": user_id,
            "store_id": store_id,
            "purchased_at": purchased_at,
            "regular_total": totals.regular_total,
            "paid_total": totals.paid_total,
            "discount_total": totals.discount_total,
            "points_earned": points_earned,
            "points_spent": points_spent,
            "counted": counted,
            "is_returned": False,
            "returned_at": None,
            "source": "api",
            "pos_id": pos_id,
        },
    )


async def _insert_items(
    conn: AsyncConnection, *, receipt_id: int, items: list[ReceiptItemDraft]
) -> list[ReceiptItemRow]:
    rows = []
    for item in items:
        rows.append(
            await database.insert_receipt_item(
                conn,
                {
                    "receipt_id": receipt_id,
                    "product_name": item.product_name,
                    "category": item.category,
                    "qty": item.qty,
                    "regular_price": item.regular_price,
                    "paid_price": item.paid_price,
                    "is_promo": item.is_promo,
                },
            )
        )
    return rows


def _to_receipt_detail(
    row: ReceiptRow, *, store_name: str, items: list[ReceiptItemRow]
) -> ReceiptDetail:
    return ReceiptDetail(
        id=row.id,
        store_id=row.store_id,
        store_name=store_name,
        purchased_at=row.purchased_at,
        regular_total=row.regular_total,
        paid_total=row.paid_total,
        discount_total=row.discount_total,
        points_earned=row.points_earned,
        points_spent=row.points_spent,
        counted=row.counted,
        is_returned=row.is_returned,
        items=items,
    )
