import re

from fastapi import APIRouter, HTTPException, Request, Query

from api.schemas import (
    FillResponse,
    HealthResponse,
    LeaderboardEntry,
    ScoreHistoryPoint,
    SnapshotPosition,
    SnapshotResponse,
    WalletDetail,
    WalletScoreResponse,
    WalletSubmission,
)

router = APIRouter(prefix="/api")

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def _db(request: Request):
    return request.app.state.db


def _serialize_row(row: dict) -> dict:
    """Convert asyncpg row values to JSON-safe types."""
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (int, float, str, bool, list)) or v is None:
            out[k] = v
        else:
            out[k] = float(v)
    return out


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("composite_score"),
    style: str | None = Query(None),
):
    db = _db(request)
    rows = await db.get_leaderboard(limit=limit, offset=offset, sort_by=sort_by, style=style)
    return [_serialize_row(r) for r in rows]


@router.get("/wallet/{address}")
async def get_wallet(request: Request, address: str):
    if not ADDRESS_RE.match(address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    wallet = await db.get_wallet(address)
    if not wallet:
        raise HTTPException(404, "Wallet not tracked")

    return _serialize_row(wallet)


@router.get("/wallet/{address}/score", response_model=WalletScoreResponse)
async def get_wallet_score(request: Request, address: str):
    if not ADDRESS_RE.match(address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    score = await db.get_score(address)
    if not score:
        raise HTTPException(404, "No score for wallet")

    return _serialize_row(score)


@router.get("/wallet/{address}/fills", response_model=list[FillResponse])
async def get_wallet_fills(
    request: Request,
    address: str,
    limit: int = Query(100, ge=1, le=2000),
):
    if not ADDRESS_RE.match(address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    rows = await db.get_fills(address, limit=limit)
    return [_serialize_row(r) for r in rows]


@router.get("/wallet/{address}/snapshot", response_model=SnapshotResponse)
async def get_wallet_snapshot(request: Request, address: str):
    if not ADDRESS_RE.match(address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    snapshot = await db.get_latest_snapshot(address)
    if not snapshot:
        raise HTTPException(404, "No snapshot for wallet")

    result = _serialize_row(snapshot)
    # Parse positions from JSONB
    positions = result.get("positions", [])
    if isinstance(positions, str):
        import json
        positions = json.loads(positions)
    result["positions"] = positions
    return result


@router.get("/wallet/{address}/history", response_model=list[ScoreHistoryPoint])
async def get_wallet_history(
    request: Request,
    address: str,
    limit: int = Query(30, ge=1, le=100),
):
    if not ADDRESS_RE.match(address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    rows = await db.get_score_history(address, limit=limit)
    return [_serialize_row(r) for r in rows]


@router.post("/wallet")
async def submit_wallet(request: Request, body: WalletSubmission):
    if not ADDRESS_RE.match(body.address):
        raise HTTPException(400, "Invalid address format")

    db = _db(request)
    status = await db.upsert_wallet(body.address, source="community", label=body.label)

    return {"address": body.address, "status": status}


@router.post("/discover/vaults")
async def discover_vaults(request: Request):
    """Scan HLP vault followers for active traders."""
    import time as _time

    db = _db(request)
    client = request.app.state.client

    # Get HLP vault followers
    try:
        data = await client._post({
            "type": "vaultDetails",
            "vaultAddress": "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303",
        })
    except Exception as e:
        raise HTTPException(502, f"Failed to query vault: {e}")

    if not data:
        return {"added": 0, "scanned": 0, "message": "No vault data returned"}

    leader = data.get("leader", "")
    followers = data.get("followers", [])
    candidates = [{"address": leader}] + [{"address": f["user"], "equity": float(f.get("vaultEquity", "0"))} for f in followers]

    added = 0
    scanned = 0
    start_90d = int((_time.time() - 90 * 86400) * 1000)

    for c in candidates:
        address = c["address"]

        # Skip if already tracked
        existing = await db.get_wallet(address)
        if existing:
            continue

        # Check for trading activity
        try:
            fills = await client.get_fills(address, start_time=start_90d)
            scanned += 1
        except Exception:
            continue

        if len(fills) >= 10:
            equity = c.get("equity", 0)
            label = f"HLP follower"
            if equity and equity > 0:
                label += f" (${equity:,.0f})"

            await db.upsert_wallet(address, source="vault_follower", label=label)
            added += 1

    return {
        "added": added,
        "scanned": scanned,
        "total_candidates": len(candidates),
        "message": f"Scanned {scanned} new addresses, added {added} active traders",
    }


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    db = _db(request)
    counts = await db.get_wallet_count()
    return {"status": "ok", "wallets": counts}
