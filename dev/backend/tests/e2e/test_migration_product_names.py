from decimal import Decimal

from psycopg import AsyncConnection

from migrate import MIGRATIONS_DIR

from .. import factories

BACKFILL_SQL = (MIGRATIONS_DIR / "004_backfill_receipt_item_names.sql").read_text(encoding="utf-8")
LEGACY_ITEMS: list[dict[str, object]] = [
    {
        "product_name": "Хлебный товар 1",
        "category": "bakery",
        "qty": Decimal("1"),
        "regular_price": Decimal("60.00"),
        "paid_price": Decimal("50.00"),
    },
    {
        "product_name": "Хлебный товар 2",
        "category": "bakery",
        "qty": Decimal("1"),
        "regular_price": Decimal("70.00"),
        "paid_price": Decimal("70.00"),
    },
    {
        "product_name": "Овощной товар 1",
        "category": "fruits_veg",
        "qty": Decimal("1"),
        "regular_price": Decimal("90.00"),
        "paid_price": Decimal("80.00"),
    },
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": Decimal("1"),
        "regular_price": Decimal("89.90"),
        "paid_price": Decimal("89.90"),
    },
]


async def _names(conn: AsyncConnection, receipt_id: int) -> list[str]:
    cur = await conn.execute(
        "SELECT product_name FROM receipt_items WHERE receipt_id = %(receipt_id)s ORDER BY id",
        {"receipt_id": receipt_id},
    )
    return [row[0] for row in await cur.fetchall()]


async def test_backfill_replaces_legacy_product_names(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id, items=LEGACY_ITEMS)

    await conn.execute(BACKFILL_SQL)

    assert await _names(conn, receipt.id) == ["Батон", "Белый хлеб", "Яблоки", "Молоко"]
