from datetime import datetime

from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.receipts.models import ReceiptItemRow, ReceiptRow

RECEIPT_LIST_SELECT = (
    "SELECT id, user_id, store_id, purchased_at, regular_total, paid_total, discount_total, "
    "points_earned, points_spent, counted, is_returned, returned_at, source, pos_id, created_at "
    "FROM receipts WHERE user_id = %(user_id)s "
    "ORDER BY purchased_at DESC, id DESC LIMIT %(limit)s"
)
RECEIPT_ITEMS_FOR_RECEIPTS_SELECT = (
    "SELECT id, receipt_id, product_name, category, qty, regular_price, paid_price, is_promo "
    "FROM receipt_items WHERE receipt_id = ANY(%(receipt_ids)s) ORDER BY receipt_id, id"
)
RECEIPT_LIST_COUNTED_SINCE_SELECT = (
    "SELECT id, user_id, store_id, purchased_at, regular_total, paid_total, discount_total, "
    "points_earned, points_spent, counted, is_returned, returned_at, source, pos_id, created_at "
    "FROM receipts WHERE user_id = %(user_id)s AND counted = true AND is_returned = false "
    "AND purchased_at >= %(since)s "
    "AND (%(until)s::timestamptz IS NULL OR purchased_at < %(until)s) "
    "ORDER BY purchased_at ASC, id ASC"
)
RECEIPT_LIST_SINCE_SELECT = (
    "SELECT id, user_id, store_id, purchased_at, regular_total, paid_total, discount_total, "
    "points_earned, points_spent, counted, is_returned, returned_at, source, pos_id, created_at "
    "FROM receipts WHERE user_id = %(user_id)s AND purchased_at >= %(since)s "
    "ORDER BY purchased_at DESC, id DESC"
)
DEDUP_WINDOW_EXISTS = (
    "SELECT EXISTS (SELECT 1 FROM receipts WHERE user_id = %(user_id)s "
    "AND store_id = %(store_id)s AND counted = true AND purchased_at > "
    "%(purchased_at)s - make_interval(mins => %(window_minutes)s) AND purchased_at < "
    "%(purchased_at)s + make_interval(mins => %(window_minutes)s))"
)
COUNTED_IN_RANGE_COUNT = (
    "SELECT count(*) FROM receipts WHERE user_id = %(user_id)s AND counted = true "
    "AND purchased_at >= %(start)s AND purchased_at < %(end)s"
)
RECEIPT_INSERT = (
    "INSERT INTO receipts (user_id, store_id, purchased_at, regular_total, paid_total, "
    "discount_total, points_earned, points_spent, counted, is_returned, returned_at, "
    "source, pos_id) "
    "VALUES (%(user_id)s, %(store_id)s, %(purchased_at)s, %(regular_total)s, %(paid_total)s, "
    "%(discount_total)s, %(points_earned)s, %(points_spent)s, %(counted)s, %(is_returned)s, "
    "%(returned_at)s, %(source)s, %(pos_id)s) "
    "RETURNING id, user_id, store_id, purchased_at, regular_total, paid_total, discount_total, "
    "points_earned, points_spent, counted, is_returned, returned_at, source, pos_id, created_at"
)
RECEIPT_UPDATE_COUNTED = (
    "UPDATE receipts SET counted = %(counted)s WHERE id = %(receipt_id)s "
    "RETURNING id, user_id, store_id, purchased_at, regular_total, paid_total, discount_total, "
    "points_earned, points_spent, counted, is_returned, returned_at, source, pos_id, created_at"
)
RECEIPT_ITEM_INSERT = (
    "INSERT INTO receipt_items (receipt_id, product_name, category, qty, "
    "regular_price, paid_price, is_promo) "
    "VALUES (%(receipt_id)s, %(product_name)s, %(category)s, %(qty)s, "
    "%(regular_price)s, %(paid_price)s, %(is_promo)s) "
    "RETURNING id, receipt_id, product_name, category, qty, regular_price, paid_price, is_promo"
)


async def insert_receipt(conn: AsyncConnection, params: dict[str, object]) -> ReceiptRow:
    async with conn.cursor(row_factory=class_row(ReceiptRow)) as cur:
        await cur.execute(RECEIPT_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def insert_receipt_item(conn: AsyncConnection, params: dict[str, object]) -> ReceiptItemRow:
    async with conn.cursor(row_factory=class_row(ReceiptItemRow)) as cur:
        await cur.execute(RECEIPT_ITEM_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def update_receipt_counted(
    conn: AsyncConnection, *, receipt_id: int, counted: bool
) -> ReceiptRow:
    async with conn.cursor(row_factory=class_row(ReceiptRow)) as cur:
        await cur.execute(RECEIPT_UPDATE_COUNTED, {"receipt_id": receipt_id, "counted": counted})
        row = await cur.fetchone()
        assert row is not None
        return row


async def list_receipts_for_user(
    conn: AsyncConnection, *, user_id: int, limit: int
) -> list[ReceiptRow]:
    async with conn.cursor(row_factory=class_row(ReceiptRow)) as cur:
        await cur.execute(RECEIPT_LIST_SELECT, {"user_id": user_id, "limit": limit})
        return await cur.fetchall()


async def list_receipt_items_for_receipts(
    conn: AsyncConnection, *, receipt_ids: list[int]
) -> list[ReceiptItemRow]:
    async with conn.cursor(row_factory=class_row(ReceiptItemRow)) as cur:
        await cur.execute(RECEIPT_ITEMS_FOR_RECEIPTS_SELECT, {"receipt_ids": receipt_ids})
        return await cur.fetchall()


async def list_counted_receipts_since(
    conn: AsyncConnection, *, user_id: int, since: datetime, until: datetime | None = None
) -> list[ReceiptRow]:
    async with conn.cursor(row_factory=class_row(ReceiptRow)) as cur:
        await cur.execute(
            RECEIPT_LIST_COUNTED_SINCE_SELECT,
            {"user_id": user_id, "since": since, "until": until},
        )
        return await cur.fetchall()


async def list_receipts_since(
    conn: AsyncConnection, *, user_id: int, since: datetime
) -> list[ReceiptRow]:
    async with conn.cursor(row_factory=class_row(ReceiptRow)) as cur:
        await cur.execute(RECEIPT_LIST_SINCE_SELECT, {"user_id": user_id, "since": since})
        return await cur.fetchall()


async def exists_counted_receipt_in_store_within_window(
    conn: AsyncConnection,
    *,
    user_id: int,
    store_id: int,
    purchased_at: datetime,
    window_minutes: int,
) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            DEDUP_WINDOW_EXISTS,
            {
                "user_id": user_id,
                "store_id": store_id,
                "purchased_at": purchased_at,
                "window_minutes": window_minutes,
            },
        )
        row = await cur.fetchone()
        return bool(row is not None and row[0])


async def count_counted_receipts_in_range(
    conn: AsyncConnection, *, user_id: int, start: datetime, end: datetime
) -> int:
    async with conn.cursor() as cur:
        await cur.execute(COUNTED_IN_RANGE_COUNT, {"user_id": user_id, "start": start, "end": end})
        row = await cur.fetchone()
        assert row is not None
        return int(row[0])
