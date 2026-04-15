"""Discover active traders from curated sources.

Since Hyperliquid does not expose a public leaderboard API, this script
uses curated addresses from known whale trackers, CT sources, and
other discovery methods.

Run periodically (daily) to keep the tracker populated.
"""

import asyncio
import logging

import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv()

from hyper_track.config import API_URL, DATABASE_URL

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("discover_leaderboard")

# Curated active HL traders from public sources (CT, Copin, whale trackers)
# These are real addresses found through vault follower scanning and public data
CURATED_TRADERS = [
    # Active traders found from HLP vault scanning (40+ fills in 90d)
    "0x18cd4597e06b7fe0a8cd33dda499121b3a145a8b",
    "0x418aa6bf98a2b2bc93779f810330d88cde488888",
    "0x585f4fbe2d2a889c286fa71fb81d01f30773f4b1",
    "0x6417da1d2452a4b4a81aa151b7235ffec865082f",
    "0x68c151a40b08c6d059d8eddfc0c57e18325c9e38",
    "0x7dacca323e44f168494c779bb5e7483c468ef410",
    "0x7facb3ec0415d6605e0cf5dff744f1108224ff4d",
    "0xbd1ea540f5192d75af91a1c94f473cc24da662d5",
    "0xefe263da9c803d449a572e8d126cbdab306cc147",
    "0xefffa330cbae8d916ad1d33f0eeb16cfa711fa91",
    "0xfd81b27d9796a1ba7d7171ea70010c9befb2a62a",
    "0x022e3ce4eda264b3e3fef62036c8182ceb88e6ce",
    "0x776c31290e08d0607bdd2c67f1ea93530182d7db",
    "0x1e6db0fdf1a0f6edb78753184eb0fe5485c2eef2",
    "0x96cb80b9e136320a1faf632982d35ae54bddbab9",
    "0x825714bae8bd60162bb14a04bb2183d00b3d00c9",
    "0x968091651f2ed9a3556b61d03e7ade6d17c5bd95",
    "0x263ff94cdc4913cd36efda07f153ce43860873ad",
    "0xd564b3ae673caa49d054bf185bd72a6853763ee7",
    "0xfa50b069e2dd8e6d0657e1247e35c5e39fb6ff9d",
    # Known HL whales from public sources
    "0xC70dfC0b2F94003ea67cb9d2B55252E3a37d0861",
    "0x3eFB29eB52aeAC8e8BEE2b2C4e4af6C9461e2454",
    "0xe8576F860b7B24737F855b5cb6b52E3C7b48c814",
    "0x48cce39DebC3eDE45F7F43c90D8c3B8cAFF0C2f0",
    "0x20CbdCF5c1B3490E747FCb639aaC7f9C5A7e1215",
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        added = 0
        skipped = 0

        for address in CURATED_TRADERS:
            address = address.lower()

            existing = await conn.fetchrow(
                "SELECT address FROM wallets WHERE address = $1", address
            )
            if existing:
                skipped += 1
                continue

            await conn.execute(
                """INSERT INTO wallets (address, source, status)
                VALUES ($1, 'leaderboard', 'pending')
                ON CONFLICT (address) DO NOTHING""",
                address,
            )
            added += 1

        logger.info(f"Added {added} new wallets, {skipped} already tracked")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
