import re
from datetime import UTC, datetime
from decimal import Decimal
from itertools import count
from typing import Any

import psycopg
import pytest
from psycopg import AsyncConnection, sql
from psycopg.conninfo import make_conninfo
from psycopg.errors import CheckViolation, ForeignKeyViolation, NumericValueOutOfRange
from psycopg.types.json import Jsonb

from app.core.config import settings
from migrate import MIGRATIONS_DIR, migrate

from . import expected_schema as schema

TEST_DSN = settings.test_database_url
WEEK_START = datetime(2026, 8, 31, tzinfo=UTC)
Row = tuple[Any, ...]
WEEK_END = datetime(2026, 9, 7, tzinfo=UTC)
CHECK_ACCEPT = [(c.table, c.column, value) for c in schema.CHECKS for value in c.accepted]
CHECK_REJECT = [(c.table, c.column, c.rejected) for c in schema.CHECKS]
NUMERIC_OVERFLOW = [("users", "social_propensity", 10), ("receipt_items", "qty", 100000)]

PARENTS: dict[str, dict[str, str]] = {
    "receipts": {"user_id": "users", "store_id": "stores"},
    "receipt_items": {"receipt_id": "receipts"},
    "user_features": {"user_id": "users"},
    "domovoy_states": {"user_id": "users"},
    "challenges": {"user_id": "users"},
    "reward_ledger": {"user_id": "users"},
}

REQUIRED_PARAMS: dict[str, dict[str, object]] = {
    "stores": {"name": "Пятёрочка", "chain": "pyaterochka", "district": "Центр", "city": "Москва"},
    "users": {"pseudonym": "Домовой-{n}", "segment": "regular_mid", "referral_code": "CODE{n}"},
    "receipts": {
        "purchased_at": WEEK_START,
        "regular_total": 600,
        "paid_total": 540,
        "discount_total": 60,
        "source": "api",
    },
    "receipt_items": {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": 1,
        "regular_price": Decimal("89.90"),
        "paid_price": Decimal("79.90"),
    },
    "user_features": {"window_weeks": 10},
    "domovoy_states": {"mood": "cozy"},
    "challenges": {
        "type": "frequency",
        "status": "active",
        "is_hero": True,
        "baseline": 2,
        "target": 3,
        "period_start": WEEK_START,
        "period_end": WEEK_END,
        "reward_xp": 50,
        "reward_points": 0,
        "economics": Jsonb({}),
        "rationale_features": Jsonb({}),
        "copy_title": "Заголовок",
        "copy_body": "Текст",
        "copy_explanation": "Почему",
        "copy_source": "template",
    },
    "reward_ledger": {"kind": "challenge"},
}

COLUMN_QUERY = (
    "SELECT column_name, data_type, is_nullable = 'YES', "
    "CASE WHEN data_type = 'numeric' THEN numeric_precision END, "
    "CASE WHEN data_type = 'numeric' THEN numeric_scale END "
    "FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %(table)s"
)
CONSTRAINT_QUERY = (
    "SELECT array_agg(kcu.column_name::text ORDER BY kcu.ordinal_position) "
    "FROM information_schema.table_constraints tc "
    "JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name) "
    "WHERE tc.constraint_type = %(kind)s AND tc.table_schema = 'public' "
    "AND tc.table_name = %(table)s GROUP BY constraint_name"
)
FOREIGN_KEY_QUERY = (
    "SELECT kcu.column_name, ccu.table_name, ccu.column_name, rc.delete_rule "
    "FROM information_schema.referential_constraints rc "
    "JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name) "
    "JOIN information_schema.constraint_column_usage ccu "
    "USING (constraint_schema, constraint_name) "
    "WHERE kcu.table_schema = 'public' AND kcu.table_name = %(table)s"
)
INDEX_QUERY = (
    "SELECT pg_get_indexdef(i.indexrelid) FROM pg_index i "
    "JOIN pg_class c ON c.oid = i.indrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE n.nspname = 'public' AND c.relname = %(table)s "
    "AND NOT EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conindid = i.indexrelid)"
)

_seq = count(1)


async def _insert_row(conn: AsyncConnection, table: str, **overrides: object) -> int:
    n = next(_seq)
    params: dict[str, object] = {
        key: value.replace("{n}", str(n)) if isinstance(value, str) else value
        for key, value in REQUIRED_PARAMS[table].items()
    }
    for column, parent in PARENTS.get(table, {}).items():
        if column not in overrides:
            params[column] = await _insert_row(conn, parent)
    params.update(overrides)
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, params)),
        sql.SQL(", ").join(map(sql.Placeholder, params)),
        sql.Identifier(schema.PRIMARY_KEYS[table][0]),
    )
    row = await _fetch_one(conn, query, **params)
    return int(row[0])


async def _make_store(conn: AsyncConnection, **overrides: object) -> int:
    return await _insert_row(conn, "stores", **overrides)


async def _make_user(conn: AsyncConnection, **overrides: object) -> int:
    return await _insert_row(conn, "users", **overrides)


async def _make_receipt(conn: AsyncConnection, **overrides: object) -> int:
    return await _insert_row(conn, "receipts", **overrides)


async def _fetch_one(conn: AsyncConnection, query: str | sql.Composed, **params: object) -> Row:
    cur = await conn.execute(query, params)
    row = await cur.fetchone()
    assert row is not None
    return tuple(row)


async def _count_rows(conn: AsyncConnection, table: str) -> int:
    row = await _fetch_one(conn, sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))
    return int(row[0])


async def _constraint_columns(conn: AsyncConnection, table: str, kind: str) -> set[tuple[str, ...]]:
    cur = await conn.execute(CONSTRAINT_QUERY, {"kind": kind, "table": table})
    return {tuple(row[0]) for row in await cur.fetchall()}


async def test_schema_migrations_table_exists(conn: AsyncConnection) -> None:
    row = await _fetch_one(conn, "SELECT to_regclass('public.schema_migrations')")
    assert row == ("schema_migrations",)


async def test_migrate_applies_all_files_on_empty_database_and_is_idempotent() -> None:
    scratch = "domovoy_migrate_scratch"
    drop = sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(scratch))
    async with await psycopg.AsyncConnection.connect(TEST_DSN, autocommit=True) as admin:
        await admin.execute(drop)
        await admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(scratch)))
        try:
            scratch_dsn = make_conninfo(TEST_DSN, dbname=scratch)
            expected = sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))
            assert await migrate(scratch_dsn) == expected
            assert await migrate(scratch_dsn) == []
        finally:
            await admin.execute(drop)


async def test_core_tables_exist(conn: AsyncConnection) -> None:
    cur = await conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    assert set(schema.TABLES) <= {row[0] for row in await cur.fetchall()}


@pytest.mark.parametrize("table", schema.TABLES)
async def test_columns_types_and_nullability(conn: AsyncConnection, table: str) -> None:
    cur = await conn.execute(COLUMN_QUERY, {"table": table})
    actual = {name: schema.Column(*rest) for name, *rest in await cur.fetchall()}
    assert actual == schema.COLUMNS[table]


@pytest.mark.parametrize("table", schema.TABLES)
async def test_primary_key(conn: AsyncConnection, table: str) -> None:
    assert await _constraint_columns(conn, table, "PRIMARY KEY") == {schema.PRIMARY_KEYS[table]}


@pytest.mark.parametrize("table", schema.TABLES)
async def test_unique_constraints(conn: AsyncConnection, table: str) -> None:
    assert await _constraint_columns(conn, table, "UNIQUE") == schema.UNIQUES.get(table, set())


@pytest.mark.parametrize("table", schema.TABLES)
async def test_foreign_keys_and_delete_rules(conn: AsyncConnection, table: str) -> None:
    cur = await conn.execute(FOREIGN_KEY_QUERY, {"table": table})
    actual = {schema.ForeignKey(*row) for row in await cur.fetchall()}
    assert actual == schema.FOREIGN_KEYS.get(table, set())


@pytest.mark.parametrize("table", schema.TABLES)
async def test_indexes(conn: AsyncConnection, table: str) -> None:
    cur = await conn.execute(INDEX_QUERY, {"table": table})
    actual = {re.sub(r"\s+", " ", row[0]).replace("public.", "") for row in await cur.fetchall()}
    expected = {index.definition(table) for index in schema.INDEXES.get(table, set())}
    assert actual == expected


@pytest.mark.parametrize(("table", "column", "value"), CHECK_ACCEPT)
async def test_check_accepts_documented_value(
    conn: AsyncConnection, table: str, column: str, value: str
) -> None:
    await _insert_row(conn, table, **{column: value})


@pytest.mark.parametrize(("table", "column", "value"), CHECK_REJECT)
async def test_check_rejects_unknown_value(
    conn: AsyncConnection, table: str, column: str, value: str
) -> None:
    with pytest.raises(CheckViolation):
        await _insert_row(conn, table, **{column: value})


@pytest.mark.parametrize("table", sorted(schema.DEFAULTS))
async def test_defaults_after_minimal_insert(conn: AsyncConnection, table: str) -> None:
    row_id = await _insert_row(conn, table)
    columns = list(schema.DEFAULTS[table])
    query = sql.SQL("SELECT {} FROM {} WHERE {} = %(id)s").format(
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.Identifier(table),
        sql.Identifier(schema.PRIMARY_KEYS[table][0]),
    )
    row = await _fetch_one(conn, query, id=row_id)
    for column, actual in zip(columns, row, strict=True):
        expected = schema.DEFAULTS[table][column]
        if expected is schema.SET_BY_DB:
            assert actual is not None, column
        else:
            assert actual == expected, column


@pytest.mark.parametrize(("table", "column", "value"), NUMERIC_OVERFLOW)
async def test_numeric_rejects_overflow(
    conn: AsyncConnection, table: str, column: str, value: int
) -> None:
    with pytest.raises(NumericValueOutOfRange):
        await _insert_row(conn, table, **{column: value})


async def test_delete_user_cascades_to_owned_rows(conn: AsyncConnection) -> None:
    user_id = await _make_user(conn)
    receipt_id = await _make_receipt(conn, user_id=user_id)
    await _insert_row(conn, "receipt_items", receipt_id=receipt_id)
    for table in ("user_features", "domovoy_states", "challenges", "reward_ledger"):
        await _insert_row(conn, table, user_id=user_id)
    await conn.execute("DELETE FROM users WHERE id = %(id)s", {"id": user_id})
    for table in PARENTS:
        assert await _count_rows(conn, table) == 0, table
    assert await _count_rows(conn, "stores") == 1


async def test_delete_store_with_receipts_is_restricted(conn: AsyncConnection) -> None:
    store_id = await _make_store(conn)
    await _make_receipt(conn, store_id=store_id)
    with pytest.raises(ForeignKeyViolation):
        await conn.execute("DELETE FROM stores WHERE id = %(id)s", {"id": store_id})


async def test_delete_store_nulls_favourite_store_references(conn: AsyncConnection) -> None:
    store_id = await _make_store(conn)
    user_id = await _make_user(conn, favourite_store_id=store_id)
    await _insert_row(conn, "user_features", user_id=user_id, favourite_store_id=store_id)
    await conn.execute("DELETE FROM stores WHERE id = %(id)s", {"id": store_id})
    users_row = await _fetch_one(
        conn, "SELECT favourite_store_id FROM users WHERE id = %(id)s", id=user_id
    )
    features_row = await _fetch_one(
        conn, "SELECT favourite_store_id FROM user_features WHERE user_id = %(id)s", id=user_id
    )
    assert (users_row, features_row) == ((None,), (None,))


async def test_delete_referrer_nulls_referred_by(conn: AsyncConnection) -> None:
    referrer_id = await _make_user(conn)
    referee_id = await _make_user(conn, referred_by_user_id=referrer_id)
    await conn.execute("DELETE FROM users WHERE id = %(id)s", {"id": referrer_id})
    row = await _fetch_one(
        conn, "SELECT referred_by_user_id FROM users WHERE id = %(id)s", id=referee_id
    )
    assert row == (None,)
