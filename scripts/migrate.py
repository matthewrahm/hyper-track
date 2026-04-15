"""Run SQL migrations against the hyper_track database."""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


async def migrate():
    database_url = os.getenv("DATABASE_URL", "postgresql://localhost/hyper_track")
    conn = await asyncpg.connect(database_url)

    try:
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for f in migration_files:
            print(f"  Running {f.name}...")
            sql = f.read_text()
            await conn.execute(sql)
            print(f"  {f.name} done")
        print("All migrations complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
