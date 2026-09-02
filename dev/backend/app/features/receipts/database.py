from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.receipts.models import ReceiptItemRow, ReceiptRow

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
