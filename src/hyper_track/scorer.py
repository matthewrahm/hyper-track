"""Wallet scoring engine.

Computes risk-adjusted performance metrics across multiple time windows,
classifies trading styles, and produces a composite score (0-100).
"""

import math
import time
from collections import defaultdict

from hyper_track.models import Fill, Trade, WindowMetrics, WalletScore


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class WalletScorer:
    """Scores wallets based on their fill history."""

    def score(
        self,
        address: str,
        fills: list[Fill],
        account_value: float = 0,
    ) -> WalletScore:
        """Compute comprehensive score across all time windows."""
        now_ms = int(time.time() * 1000)
        trades = self._group_into_trades(fills)

        w30d = self._compute_window(trades, now_ms, days=30)
        w90d = self._compute_window(trades, now_ms, days=90)
        wall = self._compute_window(trades, now_ms, days=None)

        style, style_tags = self._classify_style(w90d, trades, fills)
        composite = self._compute_composite(w90d)

        active_since = min(t.open_time for t in trades) if trades else 0
        first_time = min(f.time for f in fills) if fills else now_ms
        active_days = max(int((now_ms - first_time) / (1000 * 86400)), 1)

        return WalletScore(
            address=address,
            scored_at=time.time(),
            w30d=w30d,
            w90d=w90d,
            wall=wall,
            composite_score=composite,
            style=style,
            style_tags=style_tags,
            account_value=account_value,
            active_since=active_since,
            active_days=active_days,
        )

    def _compute_window(
        self, trades: list[Trade], now_ms: int, days: int | None
    ) -> WindowMetrics:
        """Compute metrics for a specific time window."""
        if days is not None:
            cutoff = now_ms - days * 86400 * 1000
            window_trades = [t for t in trades if t.close_time >= cutoff]
        else:
            window_trades = trades

        if not window_trades:
            return WindowMetrics(
                pnl=0, roi=0, win_rate=0, trades=0, sharpe=0, sortino=0,
                max_drawdown=0, profit_factor=0, reward_risk=0,
                avg_hold_hours=0, trades_per_day=0,
            )

        total_pnl = sum(t.net_pnl for t in window_trades)
        winning = [t for t in window_trades if t.net_pnl > 0]
        losing = [t for t in window_trades if t.net_pnl < 0]
        win_rate = len(winning) / len(window_trades)

        # ROI: time-weighted average capital
        avg_capital = self._avg_capital(window_trades)
        roi = total_pnl / avg_capital if avg_capital > 0 else 0

        # Win/loss metrics
        avg_win = sum(t.net_pnl for t in winning) / len(winning) if winning else 0
        avg_loss = sum(abs(t.net_pnl) for t in losing) / len(losing) if losing else 0
        reward_risk = avg_win / avg_loss if avg_loss > 0 else 0

        gross_profit = sum(t.net_pnl for t in winning)
        gross_loss = abs(sum(t.net_pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        max_drawdown = self._compute_drawdown(window_trades)
        sharpe = self._compute_sharpe(window_trades)
        sortino = self._compute_sortino(window_trades)

        hold_times = [t.hold_time_hours for t in window_trades if t.hold_time_hours > 0]
        avg_hold = sum(hold_times) / len(hold_times) if hold_times else 0

        first_time = min(t.open_time for t in window_trades)
        last_time = max(t.close_time for t in window_trades)
        span_days = max((last_time - first_time) / (1000 * 86400), 1)
        freq = len(window_trades) / span_days

        return WindowMetrics(
            pnl=total_pnl,
            roi=roi,
            win_rate=win_rate,
            trades=len(window_trades),
            sharpe=sharpe,
            sortino=sortino,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            reward_risk=reward_risk,
            avg_hold_hours=avg_hold,
            trades_per_day=freq,
        )

    def _group_into_trades(self, fills: list[Fill]) -> list[Trade]:
        """Group fills into round-trip trades by coin.

        A trade opens when position goes from 0 to non-zero,
        and closes when it returns to 0 (or crosses zero).
        """
        fills = sorted(fills, key=lambda f: f.time)
        positions: dict[str, dict] = defaultdict(lambda: {
            "net_size": 0.0,
            "fills": [],
            "entry_prices": [],
            "entry_sizes": [],
        })
        trades = []

        for fill in fills:
            coin = fill.coin
            pos = positions[coin]
            signed_size = fill.size if fill.side == "B" else -fill.size

            prev_net = pos["net_size"]
            pos["net_size"] += signed_size
            pos["fills"].append(fill)

            if prev_net == 0 and pos["net_size"] != 0:
                pos["entry_prices"] = [fill.price]
                pos["entry_sizes"] = [fill.size]
                pos["open_time"] = fill.time

            elif prev_net != 0 and (prev_net > 0) == (pos["net_size"] > 0) and abs(pos["net_size"]) > abs(prev_net):
                pos["entry_prices"].append(fill.price)
                pos["entry_sizes"].append(fill.size)

            if (prev_net > 0 and pos["net_size"] <= 0) or (prev_net < 0 and pos["net_size"] >= 0):
                total_entry_size = sum(pos["entry_sizes"])
                if total_entry_size > 0:
                    avg_entry = sum(
                        p * s for p, s in zip(pos["entry_prices"], pos["entry_sizes"])
                    ) / total_entry_size
                else:
                    avg_entry = fill.price

                side = "LONG" if prev_net > 0 else "SHORT"
                trade_size = abs(prev_net)
                open_time = pos.get("open_time", fill.time)

                trade_pnl = sum(f.closed_pnl for f in pos["fills"])
                trade_fees = sum(f.fee for f in pos["fills"])
                hold_hours = (fill.time - open_time) / (1000 * 3600)

                trades.append(Trade(
                    coin=coin,
                    side=side,
                    entry_price=avg_entry,
                    exit_price=fill.price,
                    size=trade_size,
                    pnl=trade_pnl,
                    fees=trade_fees,
                    net_pnl=trade_pnl - trade_fees,
                    open_time=open_time,
                    close_time=fill.time,
                    hold_time_hours=max(hold_hours, 0),
                ))

                pos["fills"] = []
                pos["entry_prices"] = []
                pos["entry_sizes"] = []

                if pos["net_size"] != 0:
                    pos["entry_prices"] = [fill.price]
                    pos["entry_sizes"] = [abs(pos["net_size"])]
                    pos["open_time"] = fill.time

        return trades

    def _avg_capital(self, trades: list[Trade]) -> float:
        """Time-weighted average deployed capital."""
        if not trades:
            return 0

        events = []
        for t in trades:
            notional = t.size * t.entry_price
            events.append((t.open_time, notional))
            events.append((t.close_time, -notional))

        events.sort(key=lambda e: e[0])

        total_weighted = 0.0
        current_capital = 0.0
        prev_time = events[0][0]

        for ts, delta in events:
            duration = ts - prev_time
            if duration > 0:
                total_weighted += current_capital * duration
            current_capital += delta
            prev_time = ts

        total_span = events[-1][0] - events[0][0]
        return total_weighted / total_span if total_span > 0 else abs(current_capital)

    def _compute_drawdown(self, trades: list[Trade]) -> float:
        """Max drawdown from cumulative PnL curve."""
        if not trades:
            return 0

        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0

        for t in sorted(trades, key=lambda t: t.close_time):
            cumulative += t.net_pnl
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / max(peak, 1) if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def _compute_sharpe(self, trades: list[Trade]) -> float:
        """Annualized Sharpe ratio from daily returns."""
        daily = self._bucket_daily_returns(trades)
        if len(daily) < 2:
            return 0

        avg = sum(daily) / len(daily)
        variance = sum((r - avg) ** 2 for r in daily) / len(daily)
        std = math.sqrt(variance) if variance > 0 else 0

        return (avg / std) * math.sqrt(365) if std > 0 else 0

    def _compute_sortino(self, trades: list[Trade]) -> float:
        """Annualized Sortino ratio from daily returns."""
        daily = self._bucket_daily_returns(trades)
        if len(daily) < 2:
            return 0

        avg = sum(daily) / len(daily)
        downside = [r for r in daily if r < 0]
        if not downside:
            return 0

        downside_dev = math.sqrt(sum(r ** 2 for r in downside) / len(downside))
        return (avg / downside_dev) * math.sqrt(365) if downside_dev > 0 else 0

    def _bucket_daily_returns(self, trades: list[Trade]) -> list[float]:
        """Aggregate trade PnL into daily buckets."""
        if not trades:
            return []

        daily: dict[int, float] = defaultdict(float)
        for t in trades:
            day_key = t.close_time // (1000 * 86400)
            daily[day_key] += t.net_pnl

        return list(daily.values())

    def _classify_style(
        self,
        metrics: WindowMetrics,
        trades: list[Trade],
        fills: list[Fill],
    ) -> tuple[str, list[str]]:
        """Classify trading style from 90d metrics."""
        avg_hold = metrics.avg_hold_hours
        freq = metrics.trades_per_day

        if avg_hold < 1 and freq > 10:
            style = "scalper"
        elif avg_hold < 24 and freq > 2:
            style = "day_trader"
        elif avg_hold < 168:
            style = "swing_trader"
        else:
            style = "position_trader"

        tags = []

        # Degen: high leverage (check fills for leverage signals, or just use style heuristics)
        if avg_hold < 0.5 and freq > 20:
            tags.append("degen")

        # Sniper: high accuracy + fast
        if metrics.win_rate > 0.7 and avg_hold < 2:
            tags.append("sniper")

        # Grinder: lots of trades, moderate win rate
        if freq > 20 and 0.45 <= metrics.win_rate <= 0.55:
            tags.append("grinder")

        # Concentration analysis
        if trades:
            coin_volumes: dict[str, float] = defaultdict(float)
            for t in trades:
                coin_volumes[t.coin] += t.size * t.entry_price
            total_vol = sum(coin_volumes.values())
            if total_vol > 0:
                max_pct = max(coin_volumes.values()) / total_vol
                if max_pct > 0.8:
                    tags.append("concentrated")
                elif len(coin_volumes) >= 10 and max_pct < 0.3:
                    tags.append("diversified")

        return style, tags

    def _compute_composite(self, metrics: WindowMetrics) -> float:
        """Composite score 0-100 from 90d metrics."""
        roi_n = clamp(metrics.roi, -1, 5) / 5
        wr_n = metrics.win_rate
        sharpe_n = clamp(metrics.sharpe, -2, 5) / 5
        sortino_n = clamp(metrics.sortino, -2, 8) / 8
        dd_n = 1 - clamp(metrics.max_drawdown, 0, 1)
        pf_n = clamp(metrics.profit_factor, 0, 5) / 5
        rr_n = clamp(metrics.reward_risk, 0, 5) / 5
        vol_n = clamp(metrics.trades / 200, 0, 1)

        composite = (
            roi_n * 0.15
            + wr_n * 0.10
            + sharpe_n * 0.15
            + sortino_n * 0.10
            + dd_n * 0.15
            + pf_n * 0.10
            + rr_n * 0.05
            + vol_n * 0.10
        )

        # Remaining 0.10 weight is longevity, but that's in the full WalletScore
        # Here we just use the metrics we have (90% of the composite)
        return round(composite / 0.90 * 100, 1) if composite > 0 else 0
