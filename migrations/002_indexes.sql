-- 002_indexes.sql -- Query-path indexes

-- Fills: primary query by address + time range
CREATE INDEX IF NOT EXISTS idx_fills_address_time ON fills (address, time_ms DESC);
CREATE INDEX IF NOT EXISTS idx_fills_coin_time ON fills (coin, time_ms DESC);

-- Wallets: polling queue
CREATE INDEX IF NOT EXISTS idx_wallets_next_poll ON wallets (next_poll_at ASC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_wallets_tier ON wallets (tier);
CREATE INDEX IF NOT EXISTS idx_wallets_cluster ON wallets (cluster_id) WHERE cluster_id IS NOT NULL;

-- Snapshots: latest per wallet
CREATE INDEX IF NOT EXISTS idx_snapshots_address_time ON wallet_snapshots (address, captured_at DESC);

-- Scores: leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_composite ON wallet_scores (composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_scores_pnl_90d ON wallet_scores (pnl_90d DESC);
CREATE INDEX IF NOT EXISTS idx_scores_style ON wallet_scores (style);

-- Score history: trend queries
CREATE INDEX IF NOT EXISTS idx_score_history_time ON score_history (scored_at DESC);
