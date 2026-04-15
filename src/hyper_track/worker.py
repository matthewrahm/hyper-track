"""Async poll worker for tracking wallets.

Runs as a standalone process (not inside FastAPI).
Manages a priority queue of wallets, polls HL for fills
and snapshots, triggers scoring, and handles backfill.
"""

import asyncio
import logging
import time

from hyper_track.client import HyperliquidClient
from hyper_track.config import (
    BACKFILL_CONCURRENCY,
    BACKFILL_DAYS,
    POLL_CONCURRENCY,
    TIER_INTERVALS,
)
from hyper_track.db import Database
from hyper_track.scorer import WalletScorer
from hyper_track.seeds import SEED_ADDRESSES

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("worker")


class PollWorker:
    """Manages wallet polling, backfill, and scoring."""

    def __init__(self):
        self.db = Database()
        self.client = HyperliquidClient()
        self.scorer = WalletScorer()
        self._rate_limiter = asyncio.Semaphore(20)  # max 20 concurrent HL requests

    async def start(self):
        """Initialize and run all worker loops."""
        await self.db.connect()
        logger.info("Worker started")

        # Seed wallets on first run
        await self._seed_wallets()

        # Run poll, backfill, and score loops concurrently
        await asyncio.gather(
            self._backfill_loop(),
            self._poll_loop(),
            self._score_loop(),
            self._refresh_loop(),
        )

    async def stop(self):
        await self.client.close()
        await self.db.close()

    async def _seed_wallets(self):
        """Insert seed addresses if not already tracked."""
        count = 0
        for addr in SEED_ADDRESSES:
            status = await self.db.upsert_wallet(addr, source="seed")
            if status == "pending":
                count += 1
        if count:
            logger.info(f"Seeded {count} new wallets")

    # -- Backfill Loop --

    async def _backfill_loop(self):
        """Continuously process wallets that need historical backfill."""
        while True:
            addresses = await self.db.get_backfill_queue(limit=BACKFILL_CONCURRENCY)
            if not addresses:
                await asyncio.sleep(10)
                continue

            tasks = [self._backfill_wallet(addr) for addr in addresses]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1)

    async def _backfill_wallet(self, address: str):
        """Fetch full history for a new wallet."""
        logger.info(f"Backfilling {address[:10]}...")
        await self.db.update_wallet_status(address, "backfilling")

        try:
            start_time = int((time.time() - BACKFILL_DAYS * 86400) * 1000)
            total_inserted = 0

            while True:
                async with self._rate_limiter:
                    fills = await self.client.get_fills(address, start_time=start_time)

                if not fills:
                    break

                inserted = await self.db.insert_fills(address, fills)
                total_inserted += inserted

                if len(fills) < 2000:
                    break

                start_time = fills[-1].time + 1

            # Get current snapshot
            async with self._rate_limiter:
                snapshot = await self.client.get_snapshot(address)
            await self.db.insert_snapshot(snapshot)

            # Update wallet to active
            fill_count = await self.db.get_fill_count(address)
            last_fill = await self.db.get_last_fill_time(address)
            tier = self._assign_tier(0, fill_count, last_fill)

            await self.db.update_wallet_status(address, "active")
            await self.db.update_wallet_tier(address, tier)
            await self.db.update_wallet_after_poll(
                address, fill_count, last_fill, TIER_INTERVALS[tier]
            )

            logger.info(
                f"Backfilled {address[:10]}: {total_inserted} fills, tier={tier}"
            )

        except Exception as e:
            logger.error(f"Backfill failed for {address[:10]}: {e}")
            await self.db.update_wallet_status(address, "pending")

    # -- Poll Loop --

    async def _poll_loop(self):
        """Continuously poll active wallets for new fills."""
        # Wait for initial backfill to populate some wallets
        await asyncio.sleep(5)

        while True:
            queue = await self.db.get_poll_queue(limit=POLL_CONCURRENCY * 2)
            if not queue:
                await asyncio.sleep(5)
                continue

            tasks = [self._poll_wallet(w) for w in queue[:POLL_CONCURRENCY]]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.5)

    async def _poll_wallet(self, wallet: dict):
        """Poll a single wallet for new fills and snapshot."""
        address = wallet["address"]

        try:
            # Get fills since last known
            last_fill_time = await self.db.get_last_fill_time(address)
            start_time = (last_fill_time + 1) if last_fill_time else int(
                (time.time() - 30 * 86400) * 1000
            )

            async with self._rate_limiter:
                new_fills = await self.client.get_fills(address, start_time=start_time)

            if new_fills:
                await self.db.insert_fills(address, new_fills)

            # Get current snapshot
            async with self._rate_limiter:
                snapshot = await self.client.get_snapshot(address)
            await self.db.insert_snapshot(snapshot)

            # Update wallet state
            fill_count = await self.db.get_fill_count(address)
            latest_fill = await self.db.get_last_fill_time(address)

            # Get current score for tier assignment
            score_row = await self.db.get_score(address)
            composite = score_row["composite_score"] if score_row else 0
            has_positions = len(snapshot.positions) > 0

            tier = self._assign_tier(composite, fill_count, latest_fill, has_positions)
            await self.db.update_wallet_tier(address, tier)
            await self.db.update_wallet_after_poll(
                address, fill_count, latest_fill, TIER_INTERVALS[tier]
            )

            if new_fills:
                logger.debug(f"Polled {address[:10]}: +{len(new_fills)} fills")

        except Exception as e:
            logger.error(f"Poll failed for {address[:10]}: {e}")

    def _assign_tier(
        self,
        composite_score: float,
        fill_count: int,
        last_fill_ms: int | None,
        has_positions: bool = False,
    ) -> str:
        """Assign polling tier based on score and activity."""
        now_ms = int(time.time() * 1000)
        if last_fill_ms is None:
            return "frozen"

        days_since = (now_ms - last_fill_ms) / (1000 * 86400)

        if days_since > 30:
            return "frozen"
        if days_since > 7 or composite_score < 40:
            return "cold"
        if composite_score >= 70 and (has_positions or days_since < 1):
            return "hot"
        return "warm"

    # -- Score Loop --

    async def _score_loop(self):
        """Periodically re-score all active wallets."""
        # Wait for backfill and initial polls
        await asyncio.sleep(30)

        while True:
            addresses = await self.db.get_all_active_wallets()
            logger.info(f"Scoring {len(addresses)} wallets...")

            for address in addresses:
                try:
                    await self._score_wallet(address)
                except Exception as e:
                    logger.error(f"Score failed for {address[:10]}: {e}")
                await asyncio.sleep(0.1)

            logger.info("Scoring round complete")
            await asyncio.sleep(30 * 60)  # Re-score every 30 min

    async def _score_wallet(self, address: str):
        """Score a single wallet from stored fills."""
        fills = await self.db.get_all_fills_for_scoring(address)
        if not fills:
            return

        account_value = 0
        snapshot = await self.db.get_latest_snapshot(address)
        if snapshot:
            account_value = float(snapshot["account_value"])

        score = self.scorer.score(address, fills, account_value)
        await self.db.upsert_score(score)
        await self.db.insert_score_history(
            address, score.composite_score, score.w30d.pnl, score.w30d.roi
        )

    # -- Refresh Loop --

    async def _refresh_loop(self):
        """Periodically refresh materialized views."""
        await asyncio.sleep(60)  # Wait for initial data
        while True:
            try:
                await self.db.refresh_leaderboard()
            except Exception as e:
                logger.error(f"Leaderboard refresh failed: {e}")
            await asyncio.sleep(5 * 60)  # Every 5 min


async def main():
    worker = PollWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
