from dataclasses import dataclass, field


@dataclass
class Fill:
    coin: str
    side: str  # "B" (buy) or "A" (sell/ask)
    price: float
    size: float
    time: int  # ms timestamp
    fee: float
    closed_pnl: float
    oid: int
    direction: str  # "Open Long", "Close Long", "Open Short", "Close Short"
    crossed: bool  # True = taker, False = maker


@dataclass
class Position:
    coin: str
    size: float
    side: str  # "LONG" or "SHORT"
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: int
    liquidation_price: float
    margin_used: float
    position_value: float


@dataclass
class WalletSnapshot:
    address: str
    account_value: float
    total_margin: float
    withdrawable: float
    positions: list[Position]


@dataclass
class Trade:
    """A round-trip trade (open to close)."""
    coin: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    fees: float
    net_pnl: float
    open_time: int  # ms timestamp
    close_time: int  # ms timestamp
    hold_time_hours: float


@dataclass
class WindowMetrics:
    """Scoring metrics for a single time window."""
    pnl: float
    roi: float
    win_rate: float
    trades: int
    sharpe: float
    sortino: float
    max_drawdown: float
    profit_factor: float
    reward_risk: float
    avg_hold_hours: float
    trades_per_day: float


@dataclass
class WalletScore:
    address: str
    scored_at: float  # unix timestamp

    # Per-window metrics
    w30d: WindowMetrics
    w90d: WindowMetrics
    wall: WindowMetrics

    # Composite
    composite_score: float  # 0-100
    style: str
    style_tags: list[str]

    # Account info
    account_value: float
    active_since: int  # ms timestamp
    active_days: int
