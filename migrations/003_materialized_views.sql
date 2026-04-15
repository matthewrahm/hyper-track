-- 003_materialized_views.sql -- Pre-computed views for fast dashboard queries

CREATE MATERIALIZED VIEW IF NOT EXISTS leaderboard AS
SELECT
    w.address,
    w.label,
    w.source,
    w.tier,
    w.last_fill_at,
    s.composite_score,
    s.pnl_30d,
    s.pnl_90d,
    s.pnl_all,
    s.roi_90d,
    s.win_rate_90d,
    s.sharpe_90d,
    s.sortino_90d,
    s.max_drawdown_90d,
    s.profit_factor_90d,
    s.reward_risk_90d,
    s.trades_90d,
    s.avg_hold_hours_90d,
    s.trades_per_day_90d,
    s.style,
    s.style_tags,
    s.account_value,
    s.scored_at,
    s.active_days,
    wc.id AS cluster_id,
    wc.primary_wallet AS cluster_primary
FROM wallet_scores s
JOIN wallets w ON w.address = s.address
LEFT JOIN wallet_clusters wc ON w.cluster_id = wc.id
WHERE w.status = 'active' AND s.trades_90d >= 5
ORDER BY s.composite_score DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leaderboard_address ON leaderboard (address);
