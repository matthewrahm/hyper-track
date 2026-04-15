"""Async Hyperliquid API client for wallet tracking."""

import time as _time

import httpx

from hyper_track.config import API_URL
from hyper_track.models import Fill, Position, WalletSnapshot


class HyperliquidClient:
    """Async client for fetching trader data from Hyperliquid."""

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=15, base_url=API_URL)

    async def close(self):
        await self._http.aclose()

    async def _post(self, payload: dict) -> dict | list:
        resp = await self._http.post("/info", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_snapshot(self, address: str) -> WalletSnapshot:
        """Fetch full account snapshot: positions, margin, equity."""
        data = await self._post({"type": "clearinghouseState", "user": address})

        positions = []
        for pos in data.get("assetPositions", []):
            p = pos.get("position", {})
            size = float(p.get("szi", "0"))
            if size == 0:
                continue

            entry = float(p.get("entryPx", "0"))
            mark = float(p.get("markPx", entry))
            notional = abs(size) * mark

            positions.append(Position(
                coin=p.get("coin", ""),
                size=abs(size),
                side="LONG" if size > 0 else "SHORT",
                entry_price=entry,
                mark_price=mark,
                unrealized_pnl=float(p.get("unrealizedPnl", "0")),
                leverage=int(float(p.get("leverage", {}).get("value", "1"))),
                liquidation_price=float(p.get("liquidationPx", "0") or "0"),
                margin_used=float(p.get("marginUsed", "0")),
                position_value=notional,
            ))

        margin = data.get("marginSummary", {})
        return WalletSnapshot(
            address=address,
            account_value=float(margin.get("accountValue", "0")),
            total_margin=float(margin.get("totalMarginUsed", "0")),
            withdrawable=float(data.get("withdrawable", "0")),
            positions=positions,
        )

    async def get_fills(self, address: str, start_time: int | None = None) -> list[Fill]:
        """Fetch trade fills from start_time. Returns up to 2000 fills."""
        if start_time is None:
            start_time = int((_time.time() - 30 * 86400) * 1000)

        raw = await self._post({
            "type": "userFillsByTime",
            "user": address,
            "startTime": start_time,
        })

        return [
            Fill(
                coin=f.get("coin", ""),
                side=f.get("side", ""),
                price=float(f.get("px", "0")),
                size=float(f.get("sz", "0")),
                time=f.get("time", 0),
                fee=float(f.get("fee", "0")),
                closed_pnl=float(f.get("closedPnl", "0")),
                oid=f.get("oid", 0),
                direction=f.get("dir", ""),
                crossed=f.get("crossed", False),
            )
            for f in raw
        ]

    async def get_all_fills(
        self, address: str, max_fills: int = 10000, days_back: int = 90
    ) -> list[Fill]:
        """Fetch all fills by paginating through time windows."""
        all_fills: list[Fill] = []
        start_time = int((_time.time() - days_back * 86400) * 1000)

        while len(all_fills) < max_fills:
            raw = await self._post({
                "type": "userFillsByTime",
                "user": address,
                "startTime": start_time,
            })

            if not raw:
                break

            for f in raw:
                all_fills.append(Fill(
                    coin=f.get("coin", ""),
                    side=f.get("side", ""),
                    price=float(f.get("px", "0")),
                    size=float(f.get("sz", "0")),
                    time=f.get("time", 0),
                    fee=float(f.get("fee", "0")),
                    closed_pnl=float(f.get("closedPnl", "0")),
                    oid=f.get("oid", 0),
                    direction=f.get("dir", ""),
                    crossed=f.get("crossed", False),
                ))

            if len(raw) < 2000:
                break

            start_time = raw[-1]["time"] + 1

        return all_fills[:max_fills]

    async def get_account_value(self, address: str) -> float:
        """Quick account value lookup."""
        data = await self._post({"type": "clearinghouseState", "user": address})
        return float(data.get("marginSummary", {}).get("accountValue", "0"))
