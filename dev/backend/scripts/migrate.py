import asyncio
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


async def migrate(dsn: str, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    applied_now: list[str] = []
    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
        await conn.execute(CREATE_TABLE)
        cur = await conn.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in await cur.fetchall()}
        for path in sorted(migrations_dir.glob("*.sql")):
            if path.name in applied:
                continue
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,)
                )
            applied_now.append(path.name)
    return applied_now


def main() -> None:
    dsn = sys.argv[1] if len(sys.argv) > 1 else settings.database_url
    applied = asyncio.run(migrate(dsn))
    print(f"applied: {applied or 'nothing new'}")


if __name__ == "__main__":
    main()
