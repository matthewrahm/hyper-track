"""asyncpg database layer for hyper-track."""

import json
import logging
from datetime import datetime, timezone

import asyncpg

from hyper_track.config import DATABASE_URL
from hyper_track.models import Fill, WalletSnapshot

logger = logging.getLogger(__name__)


class Database:
    """Async Postgres connection pool and query methods."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        logger.info("Database pool connected")

    async def close(self):
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")

    @property
    def pool(self) -> asyncpg.Pool:
        assert self._pool is not None, "Database not connected"
        return self._pool

    # -- Wallets --

    async def upsert_wallet(
        self, address: str, source: str = "community", label: str | None = None
    ) -> str:
        """Insert or update a tracked wallet. Returns status."""
        row = await self.pool.fetchrow(
            "SELECT status FROM wallets WHERE address = $1", address
        )
        if row:
            return row["status"]

        await self.pool.execute(
            """INSERT INTO wallets (address, source, label, status)
            VALUES ($1, $2, $3, 'pending')
            ON CONFLICT (address) DO NOTHING""",
            address, source, label,
        )
        return "pending"

    async def get_wallet(self, address: str) -> dict | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM wallets WHERE address = $1", address
        )
        return dict(row) if row else None

    async def get_poll_queue(self, limit: int = 100) -> list[dict]:
        """Get wallets due for polling, ordered by priority."""
        rows = await self.pool.fetch(
            """SELECT address, tier, last_polled_at, last_fill_at, fill_count
            FROM wallets
            WHERE status = 'active' AND next_poll_at <= NOW()
            ORDER BY next_poll_at ASC
            LIMIT $1""",
            limit,
        )
        return [dict(r) for r in rows]

    async def get_backfill_queue(self, limit: int = 10) -> list[str]:
        """Get wallets needing backfill."""
        rows = await self.pool.fetch(
            """SELECT address FROM wallets
            WHERE status = 'pending' OR status = 'backfilling'
            ORDER BY discovered_at ASC
            LIMIT $1""",
            limit,
        )
        return [r["address"] for r in rows]

    async def update_wallet_status(self, address: str, status: str):
        await self.pool.execute(
            "UPDATE wallets SET status = $2 WHERE address = $1",
            address, status,
        )

    async def update_wallet_after_poll(
        self,
        address: str,
        fill_count: int,
        last_fill_at: int | None,
        next_poll_seconds: int,
    ):
        """Update wallet metadata after a successful poll."""
        last_fill_ts = (
            datetime.fromtimestamp(last_fill_at / 1000, tz=timezone.utc)
            if last_fill_at
            else None
        )
        await self.pool.execute(
            """UPDATE wallets SET
                last_polled_at = NOW(),
                last_fill_at = COALESCE($2, last_fill_at),
                fill_count = $3,
                next_poll_at = NOW() + ($4 || ' seconds')::INTERVAL
            WHERE address = $1""",
            address, last_fill_ts, fill_count, str(next_poll_seconds),
        )

    async def update_wallet_tier(self, address: str, tier: str):
        await self.pool.execute(
            "UPDATE wallets SET tier = $2 WHERE address = $1",
            address, tier,
        )

    async def get_all_active_wallets(self) -> list[str]:
        rows = await self.pool.fetch(
            "SELECT address FROM wallets WHERE status = 'active'"
        )
        return [r["address"] for r in rows]

    async def get_wallet_count(self) -> dict:
        row = await self.pool.fetchrow(
            """SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'active') AS active,
                COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                COUNT(*) FILTER (WHERE status = 'backfilling') AS backfilling
            FROM wallets"""
        )
        return dict(row)

    # -- Fills --

    async def insert_fills(self, address: str, fills: list[Fill]) -> int:
        """Bulk insert fills, skip duplicates. Returns count inserted."""
        if not fills:
            return 0

        records = [
            (address, f.coin, f.side, f.price, f.size, f.time,
             f.fee, f.closed_pnl, f.oid, f.direction, f.crossed)
            for f in fills
        ]

        result = await self.pool.executemany(
            """INSERT INTO fills
            (address, coin, side, price, size, time_ms, fee, closed_pnl, oid, direction, crossed)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (time_ms, address, oid) DO NOTHING""",
            records,
        )
        return len(fills)

    async def get_fills(
        self, address: str, start_time_ms: int | None = None, limit: int = 2000
    ) -> list[dict]:
        """Get fills for a wallet, optionally from a start time."""
        if start_time_ms:
            rows = await self.pool.fetch(
                """SELECT * FROM fills
                WHERE address = $1 AND time_ms >= $2
                ORDER BY time_ms ASC LIMIT $3""",
                address, start_time_ms, limit,
            )
        else:
            rows = await self.pool.fetch(
                """SELECT * FROM fills
                WHERE address = $1
                ORDER BY time_ms DESC LIMIT $2""",
                address, limit,
            )
        return [dict(r) for r in rows]

    async def get_all_fills_for_scoring(self, address: str) -> list[Fill]:
        """Get all fills for a wallet as Fill objects (for scoring)."""
        rows = await self.pool.fetch(
            """SELECT coin, side, price, size, time_ms, fee, closed_pnl,
                      oid, direction, crossed
            FROM fills WHERE address = $1 ORDER BY time_ms ASC""",
            address,
        )
        return [
            Fill(
                coin=r["coin"],
                side=r["side"],
                price=float(r["price"]),
                size=float(r["size"]),
                time=r["time_ms"],
                fee=float(r["fee"]),
                closed_pnl=float(r["closed_pnl"]),
                oid=r["oid"],
                direction=r["direction"] or "",
                crossed=r["crossed"],
            )
            for r in rows
        ]

    async def get_last_fill_time(self, address: str) -> int | None:
        """Get the latest fill time_ms for a wallet."""
        row = await self.pool.fetchrow(
            "SELECT MAX(time_ms) AS last FROM fills WHERE address = $1",
            address,
        )
        return row["last"] if row and row["last"] else None

    async def get_fill_count(self, address: str) -> int:
        row = await self.pool.fetchrow(
            "SELECT COUNT(*) AS cnt FROM fills WHERE address = $1",
            address,
        )
        return row["cnt"]

    # -- Snapshots --

    async def insert_snapshot(self, snapshot: WalletSnapshot):
        """Insert a wallet snapshot."""
        positions_json = json.dumps([
            {
                "coin": p.coin, "size": p.size, "side": p.side,
                "entry_price": p.entry_price, "mark_price": p.mark_price,
                "unrealized_pnl": p.unrealized_pnl, "leverage": p.leverage,
                "liquidation_price": p.liquidation_price,
                "margin_used": p.margin_used, "position_value": p.position_value,
            }
            for p in snapshot.positions
        ])
        await self.pool.execute(
            """INSERT INTO wallet_snapshots
            (address, account_value, total_margin, withdrawable, positions)
            VALUES ($1, $2, $3, $4, $5::jsonb)""",
            snapshot.address, snapshot.account_value,
            snapshot.total_margin, snapshot.withdrawable, positions_json,
        )

    async def get_latest_snapshot(self, address: str) -> dict | None:
        row = await self.pool.fetchrow(
            """SELECT * FROM wallet_snapshots
            WHERE address = $1 ORDER BY captured_at DESC LIMIT 1""",
            address,
        )
        return dict(row) if row else None

    # -- Scores --

    async def upsert_score(self, score: "WalletScore"):
        """Insert or update wallet score."""
        from hyper_track.models import WalletScore
        await self.pool.execute(
            """INSERT INTO wallet_scores (
                address, scored_at,
                pnl_30d, roi_30d, win_rate_30d, trades_30d, sharpe_30d, sortino_30d,
                max_drawdown_30d, profit_factor_30d, reward_risk_30d,
                avg_hold_hours_30d, trades_per_day_30d,
                pnl_90d, roi_90d, win_rate_90d, trades_90d, sharpe_90d, sortino_90d,
                max_drawdown_90d, profit_factor_90d, reward_risk_90d,
                avg_hold_hours_90d, trades_per_day_90d,
                pnl_all, roi_all, win_rate_all, trades_all, sharpe_all, sortino_all,
                max_drawdown_all, profit_factor_all, reward_risk_all,
                avg_hold_hours_all, trades_per_day_all,
                composite_score, style, style_tags,
                account_value, active_since, active_days
            ) VALUES (
                $1, NOW(),
                $2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,
                $13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,
                $24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,
                $35,$36,$37,$38,$39,$40
            )
            ON CONFLICT (address) DO UPDATE SET
                scored_at = NOW(),
                pnl_30d=$2, roi_30d=$3, win_rate_30d=$4, trades_30d=$5,
                sharpe_30d=$6, sortino_30d=$7, max_drawdown_30d=$8,
                profit_factor_30d=$9, reward_risk_30d=$10,
                avg_hold_hours_30d=$11, trades_per_day_30d=$12,
                pnl_90d=$13, roi_90d=$14, win_rate_90d=$15, trades_90d=$16,
                sharpe_90d=$17, sortino_90d=$18, max_drawdown_90d=$19,
                profit_factor_90d=$20, reward_risk_90d=$21,
                avg_hold_hours_90d=$22, trades_per_day_90d=$23,
                pnl_all=$24, roi_all=$25, win_rate_all=$26, trades_all=$27,
                sharpe_all=$28, sortino_all=$29, max_drawdown_all=$30,
                profit_factor_all=$31, reward_risk_all=$32,
                avg_hold_hours_all=$33, trades_per_day_all=$34,
                composite_score=$35, style=$36, style_tags=$37,
                account_value=$38, active_since=$39, active_days=$40""",
            score.address,
            score.w30d.pnl, score.w30d.roi, score.w30d.win_rate, score.w30d.trades,
            score.w30d.sharpe, score.w30d.sortino, score.w30d.max_drawdown,
            score.w30d.profit_factor, score.w30d.reward_risk,
            score.w30d.avg_hold_hours, score.w30d.trades_per_day,
            score.w90d.pnl, score.w90d.roi, score.w90d.win_rate, score.w90d.trades,
            score.w90d.sharpe, score.w90d.sortino, score.w90d.max_drawdown,
            score.w90d.profit_factor, score.w90d.reward_risk,
            score.w90d.avg_hold_hours, score.w90d.trades_per_day,
            score.wall.pnl, score.wall.roi, score.wall.win_rate, score.wall.trades,
            score.wall.sharpe, score.wall.sortino, score.wall.max_drawdown,
            score.wall.profit_factor, score.wall.reward_risk,
            score.wall.avg_hold_hours, score.wall.trades_per_day,
            score.composite_score, score.style, score.style_tags,
            score.account_value,
            datetime.fromtimestamp(score.active_since / 1000, tz=timezone.utc) if score.active_since else None,
            score.active_days,
        )

    async def insert_score_history(self, address: str, composite: float, pnl_30d: float, roi_30d: float):
        await self.pool.execute(
            """INSERT INTO score_history (address, scored_at, composite_score, pnl_30d, roi_30d)
            VALUES ($1, NOW(), $2, $3, $4)""",
            address, composite, pnl_30d, roi_30d,
        )

    async def get_score(self, address: str) -> dict | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM wallet_scores WHERE address = $1", address
        )
        return dict(row) if row else None

    async def get_score_history(self, address: str, limit: int = 30) -> list[dict]:
        rows = await self.pool.fetch(
            """SELECT scored_at, composite_score, pnl_30d, roi_30d
            FROM score_history WHERE address = $1
            ORDER BY scored_at DESC LIMIT $2""",
            address, limit,
        )
        return [dict(r) for r in rows]

    # -- Leaderboard --

    async def get_leaderboard(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "composite_score",
        style: str | None = None,
    ) -> list[dict]:
        """Query leaderboard materialized view."""
        allowed_sorts = {
            "composite_score", "pnl_30d", "pnl_90d", "pnl_all",
            "roi_90d", "sharpe_90d", "sortino_90d", "win_rate_90d",
            "trades_90d", "profit_factor_90d",
        }
        if sort_by not in allowed_sorts:
            sort_by = "composite_score"

        if style:
            rows = await self.pool.fetch(
                f"""SELECT * FROM leaderboard
                WHERE style = $1
                ORDER BY {sort_by} DESC NULLS LAST
                LIMIT $2 OFFSET $3""",
                style, limit, offset,
            )
        else:
            rows = await self.pool.fetch(
                f"""SELECT * FROM leaderboard
                ORDER BY {sort_by} DESC NULLS LAST
                LIMIT $1 OFFSET $2""",
                limit, offset,
            )
        return [dict(r) for r in rows]

    async def refresh_leaderboard(self):
        """Refresh the materialized view concurrently."""
        await self.pool.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard"
        )
        logger.info("Leaderboard materialized view refreshed")
