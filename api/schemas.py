from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    address: str
    label: str | None
    source: str
    tier: str
    last_fill_at: str | None
    composite_score: float
    pnl_30d: float | None
    pnl_90d: float | None
    pnl_all: float | None
    roi_90d: float | None
    win_rate_90d: float | None
    sharpe_90d: float | None
    sortino_90d: float | None
    max_drawdown_90d: float | None
    profit_factor_90d: float | None
    reward_risk_90d: float | None
    trades_90d: int | None
    avg_hold_hours_90d: float | None
    trades_per_day_90d: float | None
    style: str | None
    style_tags: list[str] | None
    account_value: float | None
    scored_at: str | None
    active_days: int | None
    cluster_id: int | None
    cluster_primary: str | None


class WalletDetail(BaseModel):
    address: str
    label: str | None
    source: str
    status: str
    tier: str
    discovered_at: str
    last_polled_at: str | None
    last_fill_at: str | None
    fill_count: int


class WalletScoreResponse(BaseModel):
    address: str
    scored_at: str
    composite_score: float
    style: str | None
    style_tags: list[str] | None
    account_value: float | None
    active_days: int | None
    # 30d
    pnl_30d: float | None
    roi_30d: float | None
    win_rate_30d: float | None
    trades_30d: int | None
    sharpe_30d: float | None
    sortino_30d: float | None
    max_drawdown_30d: float | None
    profit_factor_30d: float | None
    reward_risk_30d: float | None
    avg_hold_hours_30d: float | None
    # 90d
    pnl_90d: float | None
    roi_90d: float | None
    win_rate_90d: float | None
    trades_90d: int | None
    sharpe_90d: float | None
    sortino_90d: float | None
    max_drawdown_90d: float | None
    profit_factor_90d: float | None
    reward_risk_90d: float | None
    avg_hold_hours_90d: float | None
    # All
    pnl_all: float | None
    roi_all: float | None
    win_rate_all: float | None
    trades_all: int | None
    sharpe_all: float | None
    sortino_all: float | None
    max_drawdown_all: float | None
    profit_factor_all: float | None
    reward_risk_all: float | None
    avg_hold_hours_all: float | None


class FillResponse(BaseModel):
    coin: str
    side: str
    price: float
    size: float
    time_ms: int
    fee: float
    closed_pnl: float
    direction: str | None
    crossed: bool


class SnapshotPosition(BaseModel):
    coin: str
    size: float
    side: str
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: int
    liquidation_price: float
    margin_used: float
    position_value: float


class SnapshotResponse(BaseModel):
    address: str
    captured_at: str
    account_value: float
    total_margin: float
    withdrawable: float
    positions: list[SnapshotPosition]


class ScoreHistoryPoint(BaseModel):
    scored_at: str
    composite_score: float
    pnl_30d: float | None
    roi_30d: float | None


class WalletSubmission(BaseModel):
    address: str
    label: str | None = None


class HealthResponse(BaseModel):
    status: str
    wallets: dict
