-- 001_initial.sql -- Core tables for hyper-track

-- Tracked wallets
CREATE TABLE IF NOT EXISTS wallets (
    address         VARCHAR(42) PRIMARY KEY,
    label           VARCHAR(128),
    source          VARCHAR(32) NOT NULL DEFAULT 'community',
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    tier            VARCHAR(8) NOT NULL DEFAULT 'cold',
    discovered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_polled_at  TIMESTAMPTZ,
    last_fill_at    TIMESTAMPTZ,
    next_poll_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fill_count      INTEGER NOT NULL DEFAULT 0,
    cluster_id      INTEGER,
    metadata        JSONB DEFAULT '{}'
);

-- Raw trade fills (partitioned by month)
CREATE TABLE IF NOT EXISTS fills (
    address         VARCHAR(42) NOT NULL,
    coin            VARCHAR(16) NOT NULL,
    side            CHAR(1) NOT NULL,
    price           NUMERIC(20,8) NOT NULL,
    size            NUMERIC(20,8) NOT NULL,
    time_ms         BIGINT NOT NULL,
    fee             NUMERIC(20,8) NOT NULL,
    closed_pnl      NUMERIC(20,8) NOT NULL DEFAULT 0,
    oid             BIGINT NOT NULL,
    direction       VARCHAR(16),
    crossed         BOOLEAN NOT NULL DEFAULT FALSE,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (time_ms, address, oid)
) PARTITION BY RANGE (time_ms);

-- Create monthly partitions: Jan 2025 through Dec 2026
CREATE TABLE IF NOT EXISTS fills_p2025_01 PARTITION OF fills FOR VALUES FROM (1735689600000) TO (1738368000000);
CREATE TABLE IF NOT EXISTS fills_p2025_02 PARTITION OF fills FOR VALUES FROM (1738368000000) TO (1740787200000);
CREATE TABLE IF NOT EXISTS fills_p2025_03 PARTITION OF fills FOR VALUES FROM (1740787200000) TO (1743465600000);
CREATE TABLE IF NOT EXISTS fills_p2025_04 PARTITION OF fills FOR VALUES FROM (1743465600000) TO (1746057600000);
CREATE TABLE IF NOT EXISTS fills_p2025_05 PARTITION OF fills FOR VALUES FROM (1746057600000) TO (1748736000000);
CREATE TABLE IF NOT EXISTS fills_p2025_06 PARTITION OF fills FOR VALUES FROM (1748736000000) TO (1751328000000);
CREATE TABLE IF NOT EXISTS fills_p2025_07 PARTITION OF fills FOR VALUES FROM (1751328000000) TO (1754006400000);
CREATE TABLE IF NOT EXISTS fills_p2025_08 PARTITION OF fills FOR VALUES FROM (1754006400000) TO (1756684800000);
CREATE TABLE IF NOT EXISTS fills_p2025_09 PARTITION OF fills FOR VALUES FROM (1756684800000) TO (1759276800000);
CREATE TABLE IF NOT EXISTS fills_p2025_10 PARTITION OF fills FOR VALUES FROM (1759276800000) TO (1761955200000);
CREATE TABLE IF NOT EXISTS fills_p2025_11 PARTITION OF fills FOR VALUES FROM (1761955200000) TO (1764547200000);
CREATE TABLE IF NOT EXISTS fills_p2025_12 PARTITION OF fills FOR VALUES FROM (1764547200000) TO (1767225600000);
CREATE TABLE IF NOT EXISTS fills_p2026_01 PARTITION OF fills FOR VALUES FROM (1767225600000) TO (1769904000000);
CREATE TABLE IF NOT EXISTS fills_p2026_02 PARTITION OF fills FOR VALUES FROM (1769904000000) TO (1772323200000);
CREATE TABLE IF NOT EXISTS fills_p2026_03 PARTITION OF fills FOR VALUES FROM (1772323200000) TO (1775001600000);
CREATE TABLE IF NOT EXISTS fills_p2026_04 PARTITION OF fills FOR VALUES FROM (1775001600000) TO (1777593600000);
CREATE TABLE IF NOT EXISTS fills_p2026_05 PARTITION OF fills FOR VALUES FROM (1777593600000) TO (1780272000000);
CREATE TABLE IF NOT EXISTS fills_p2026_06 PARTITION OF fills FOR VALUES FROM (1780272000000) TO (1782864000000);
CREATE TABLE IF NOT EXISTS fills_p2026_07 PARTITION OF fills FOR VALUES FROM (1782864000000) TO (1785542400000);
CREATE TABLE IF NOT EXISTS fills_p2026_08 PARTITION OF fills FOR VALUES FROM (1785542400000) TO (1788220800000);
CREATE TABLE IF NOT EXISTS fills_p2026_09 PARTITION OF fills FOR VALUES FROM (1788220800000) TO (1790812800000);
CREATE TABLE IF NOT EXISTS fills_p2026_10 PARTITION OF fills FOR VALUES FROM (1790812800000) TO (1793491200000);
CREATE TABLE IF NOT EXISTS fills_p2026_11 PARTITION OF fills FOR VALUES FROM (1793491200000) TO (1796083200000);
CREATE TABLE IF NOT EXISTS fills_p2026_12 PARTITION OF fills FOR VALUES FROM (1796083200000) TO (1798761600000);

-- Periodic account snapshots
CREATE TABLE IF NOT EXISTS wallet_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    address         VARCHAR(42) NOT NULL,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    account_value   NUMERIC(20,4) NOT NULL,
    total_margin    NUMERIC(20,4) NOT NULL,
    withdrawable    NUMERIC(20,4) NOT NULL,
    positions       JSONB NOT NULL DEFAULT '[]',
    UNIQUE(address, captured_at)
);

-- Computed scores per wallet
CREATE TABLE IF NOT EXISTS wallet_scores (
    address             VARCHAR(42) PRIMARY KEY REFERENCES wallets(address),
    scored_at           TIMESTAMPTZ NOT NULL,

    -- 30-day window
    pnl_30d             NUMERIC(20,4),
    roi_30d             NUMERIC(10,6),
    win_rate_30d        NUMERIC(5,4),
    trades_30d          INTEGER,
    sharpe_30d          NUMERIC(8,4),
    sortino_30d         NUMERIC(8,4),
    max_drawdown_30d    NUMERIC(5,4),
    profit_factor_30d   NUMERIC(8,4),
    reward_risk_30d     NUMERIC(8,4),
    avg_hold_hours_30d  NUMERIC(10,2),
    trades_per_day_30d  NUMERIC(8,4),

    -- 90-day window
    pnl_90d             NUMERIC(20,4),
    roi_90d             NUMERIC(10,6),
    win_rate_90d        NUMERIC(5,4),
    trades_90d          INTEGER,
    sharpe_90d          NUMERIC(8,4),
    sortino_90d         NUMERIC(8,4),
    max_drawdown_90d    NUMERIC(5,4),
    profit_factor_90d   NUMERIC(8,4),
    reward_risk_90d     NUMERIC(8,4),
    avg_hold_hours_90d  NUMERIC(10,2),
    trades_per_day_90d  NUMERIC(8,4),

    -- All-time
    pnl_all             NUMERIC(20,4),
    roi_all             NUMERIC(10,6),
    win_rate_all        NUMERIC(5,4),
    trades_all          INTEGER,
    sharpe_all          NUMERIC(8,4),
    sortino_all         NUMERIC(8,4),
    max_drawdown_all    NUMERIC(5,4),
    profit_factor_all   NUMERIC(8,4),
    reward_risk_all     NUMERIC(8,4),
    avg_hold_hours_all  NUMERIC(10,2),
    trades_per_day_all  NUMERIC(8,4),

    -- Composite
    composite_score     NUMERIC(5,1) NOT NULL DEFAULT 0,
    style               VARCHAR(24),
    style_tags          TEXT[],

    -- Account info at score time
    account_value       NUMERIC(20,4),
    active_since        TIMESTAMPTZ,
    active_days         INTEGER
);

-- Sybil clustering
CREATE TABLE IF NOT EXISTS wallet_clusters (
    id              SERIAL PRIMARY KEY,
    label           VARCHAR(128),
    primary_wallet  VARCHAR(42) REFERENCES wallets(address),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Wallet relationships (leader/follower, sybil)
CREATE TABLE IF NOT EXISTS wallet_relationships (
    id              SERIAL PRIMARY KEY,
    wallet_a        VARCHAR(42) NOT NULL REFERENCES wallets(address),
    wallet_b        VARCHAR(42) NOT NULL REFERENCES wallets(address),
    relationship    VARCHAR(16) NOT NULL,
    confidence      NUMERIC(5,4) NOT NULL,
    avg_delay_ms    INTEGER,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(wallet_a, wallet_b, relationship)
);

-- Score history for trend sparklines
CREATE TABLE IF NOT EXISTS score_history (
    address         VARCHAR(42) NOT NULL,
    scored_at       TIMESTAMPTZ NOT NULL,
    composite_score NUMERIC(5,1) NOT NULL,
    pnl_30d         NUMERIC(20,4),
    roi_30d         NUMERIC(10,6),
    PRIMARY KEY (address, scored_at)
);
