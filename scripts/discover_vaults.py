"""Discover active traders from Hyperliquid vault followers.

Queries the HLP vault (and any other known vaults), extracts follower
addresses, checks each for trading activity, and inserts active
traders into the wallets table.
"""

import asyncio
import logging
import time

import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv()

from hyper_track.config import API_URL, DATABASE_URL

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("discover_vaults")

# Known vault addresses to scan
VAULT_ADDRESSES = [
    "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303",  # HLP (main market-making vault)
]

# Minimum fills in last 90 days to be considered an active trader
MIN_FILLS = 10


async def get_vault_followers(client: httpx.AsyncClient, vault_address: str) -> list[dict]:
    """Fetch followers of a vault."""
    r = await client.post(f"{API_URL}/info", json={
        "type": "vaultDetails",
        "vaultAddress": vault_address,
    })
    r.raise_for_status()
    data = r.json()
    if not data:
        return []

    vault_name = data.get("name", "Unknown")
    leader = data.get("leader", "")
    followers = data.get("followers", [])

    logger.info(f"Vault '{vault_name}': leader={leader[:10]}..., {len(followers)} followers")

    result = [{"address": leader, "vault_equity": 0, "vault_name": vault_name}]
    for f in followers:
        result.append({
            "address": f["user"],
            "vault_equity": float(f.get("vaultEquity", "0")),
            "vault_name": vault_name,
        })
    return result


async def check_trading_activity(
    client: httpx.AsyncClient, address: str, semaphore: asyncio.Semaphore
) -> int:
    """Check how many fills an address has in the last 90 days."""
    async with semaphore:
        start_time = int((time.time() - 90 * 86400) * 1000)
        r = await client.post(f"{API_URL}/info", json={
            "type": "userFillsByTime",
            "user": address,
            "startTime": start_time,
        })
        r.raise_for_status()
        return len(r.json())


async def main():
    client = httpx.AsyncClient(timeout=15)
    conn = await asyncpg.connect(DATABASE_URL)
    semaphore = asyncio.Semaphore(10)  # Rate limit

    try:
        total_discovered = 0

        for vault_addr in VAULT_ADDRESSES:
            logger.info(f"Scanning vault {vault_addr[:10]}...")
            candidates = await get_vault_followers(client, vault_addr)

            logger.info(f"Checking {len(candidates)} addresses for trading activity...")

            for i, c in enumerate(candidates):
                address = c["address"]

                # Skip if already tracked
                existing = await conn.fetchrow(
                    "SELECT address FROM wallets WHERE address = $1", address
                )
                if existing:
                    continue

                fill_count = await check_trading_activity(client, address, semaphore)

                if fill_count >= MIN_FILLS:
                    label = f"{c['vault_name']} follower"
                    if c["vault_equity"] > 0:
                        label += f" (${c['vault_equity']:,.0f})"

                    await conn.execute(
                        """INSERT INTO wallets (address, source, label, status)
                        VALUES ($1, 'vault_follower', $2, 'pending')
                        ON CONFLICT (address) DO NOTHING""",
                        address, label,
                    )
                    total_discovered += 1
                    logger.info(
                        f"  Added {address[:10]}... ({fill_count} fills, {label})"
                    )

                if (i + 1) % 20 == 0:
                    logger.info(f"  Checked {i + 1}/{len(candidates)} addresses")

        logger.info(f"Discovery complete. Added {total_discovered} new wallets.")

    finally:
        await conn.close()
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
