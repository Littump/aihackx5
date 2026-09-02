import re

import pytest
from psycopg import AsyncConnection

from . import expected_schema as schema

CHECK_DEFS_QUERY = (
    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
    "WHERE conrelid = %(table)s::regclass AND contype = 'c'"
)
CHECK_DEFINITIONS = [(c.table, c.column, c.accepted) for c in schema.CHECK_VALUES]
DEFAULT_QUERY = (
    "SELECT column_default FROM information_schema.columns "
    "WHERE table_schema = 'public' AND table_name = %(table)s AND column_name = %(column)s"
)
DEFAULT_VALUES = [
    ("leagues", "status", "'open'::text"),
    ("league_members", "score", "0"),
    ("referrals", "status", "'pending'::text"),
    ("referrals", "fraud_reasons", "'[]'::jsonb"),
    ("referrals", "referrer_reward_points", "0"),
    ("referrals", "referee_reward_points", "0"),
]


def _accepted_values(definitions: list[str], column: str) -> list[str]:
    matching = [d for d in definitions if re.search(rf"\b{re.escape(column)}\b", d)]
    assert len(matching) == 1, (column, definitions)
    return sorted(re.findall(r"'([^']*)'::text", matching[0]))


@pytest.mark.parametrize(("table", "column", "accepted"), CHECK_DEFINITIONS)
async def test_check_constraint_matches_documented_values(
    conn: AsyncConnection, table: str, column: str, accepted: tuple[str, ...]
) -> None:
    cur = await conn.execute(CHECK_DEFS_QUERY, {"table": table})
    definitions = [row[0] for row in await cur.fetchall()]
    assert _accepted_values(definitions, column) == sorted(accepted)


@pytest.mark.parametrize(("table", "column", "expected"), DEFAULT_VALUES)
async def test_column_default_matches_documented_value(
    conn: AsyncConnection, table: str, column: str, expected: str
) -> None:
    cur = await conn.execute(DEFAULT_QUERY, {"table": table, "column": column})
    row = await cur.fetchone()
    assert row is not None
    assert row[0] == expected
