from psycopg import AsyncConnection


async def test_schema_migrations_table_exists(conn: AsyncConnection) -> None:
    cur = await conn.execute("SELECT to_regclass('public.schema_migrations')")
    row = await cur.fetchone()
    assert row is not None and row[0] == "schema_migrations"
