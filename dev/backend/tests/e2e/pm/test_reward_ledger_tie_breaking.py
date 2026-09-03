from datetime import UTC, datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.factories import make_user

TIED_CREATED_AT = datetime(2026, 9, 15, 12, 0, 0, tzinfo=UTC)
ENTRIES_COUNT = 25
LEDGER_LIMIT = 20


async def _insert_ledger_entry_with_fixed_timestamp(
    conn: AsyncConnection, *, user_id: int, xp_delta: int, created_at: datetime
) -> None:
    await conn.execute(
        "INSERT INTO reward_ledger (user_id, kind, xp_delta, points_delta, created_at) "
        "VALUES (%(user_id)s, 'receipt_xp', %(xp_delta)s, 0, %(created_at)s)",
        {"user_id": user_id, "xp_delta": xp_delta, "created_at": created_at},
    )


async def test_reward_ledger_last_20_prefers_most_recently_inserted_entries_on_tied_timestamps(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    # DEF-1: REWARD_LEDGER_LIST_FOR_USER orders only by created_at, no id tiebreak
    user = await make_user(conn)
    for i in range(1, ENTRIES_COUNT + 1):
        await _insert_ledger_entry_with_fixed_timestamp(
            conn, user_id=user.id, xp_delta=i, created_at=TIED_CREATED_AT
        )

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    xp_deltas = {entry["xp_delta"] for entry in response.json()["ledger"]}
    most_recently_inserted = set(range(ENTRIES_COUNT - LEDGER_LIMIT + 1, ENTRIES_COUNT + 1))
    assert xp_deltas == most_recently_inserted
