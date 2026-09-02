from psycopg import AsyncConnection


async def ping(conn: AsyncConnection) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1")
        row = await cur.fetchone()
        return row is not None and row[0] == 1
