const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003";

export interface LeaderboardEntry {
  address: string;
  label: string | null;
  source: string;
  tier: string;
  last_fill_at: string | null;
  composite_score: number;
  pnl_30d: number | null;
  pnl_90d: number | null;
  pnl_all: number | null;
  roi_90d: number | null;
  win_rate_90d: number | null;
  sharpe_90d: number | null;
  sortino_90d: number | null;
  max_drawdown_90d: number | null;
  profit_factor_90d: number | null;
  reward_risk_90d: number | null;
  trades_90d: number | null;
  avg_hold_hours_90d: number | null;
  trades_per_day_90d: number | null;
  style: string | null;
  style_tags: string[] | null;
  account_value: number | null;
  scored_at: string | null;
  active_days: number | null;
  cluster_id: number | null;
  cluster_primary: string | null;
}

export interface WalletScore {
  address: string;
  scored_at: string;
  composite_score: number;
  style: string | null;
  style_tags: string[] | null;
  account_value: number | null;
  active_days: number | null;
  pnl_30d: number | null;
  roi_30d: number | null;
  win_rate_30d: number | null;
  trades_30d: number | null;
  sharpe_30d: number | null;
  sortino_30d: number | null;
  max_drawdown_30d: number | null;
  profit_factor_30d: number | null;
  reward_risk_30d: number | null;
  avg_hold_hours_30d: number | null;
  pnl_90d: number | null;
  roi_90d: number | null;
  win_rate_90d: number | null;
  trades_90d: number | null;
  sharpe_90d: number | null;
  sortino_90d: number | null;
  max_drawdown_90d: number | null;
  profit_factor_90d: number | null;
  reward_risk_90d: number | null;
  avg_hold_hours_90d: number | null;
  pnl_all: number | null;
  roi_all: number | null;
  win_rate_all: number | null;
  trades_all: number | null;
  sharpe_all: number | null;
  sortino_all: number | null;
  max_drawdown_all: number | null;
  profit_factor_all: number | null;
  reward_risk_all: number | null;
  avg_hold_hours_all: number | null;
}

export interface WalletFill {
  coin: string;
  side: string;
  price: number;
  size: number;
  time_ms: number;
  fee: number;
  closed_pnl: number;
  direction: string | null;
  crossed: boolean;
}

export interface SnapshotPosition {
  coin: string;
  size: number;
  side: string;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  leverage: number;
  liquidation_price: number;
  margin_used: number;
  position_value: number;
}

export interface WalletSnapshot {
  address: string;
  captured_at: string;
  account_value: number;
  total_margin: number;
  withdrawable: number;
  positions: SnapshotPosition[];
}

export interface ScoreHistoryPoint {
  scored_at: string;
  composite_score: number;
  pnl_30d: number | null;
  roi_30d: number | null;
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export function getLeaderboard(
  limit = 50,
  sortBy = "composite_score",
  style?: string
) {
  let url = `/api/leaderboard?limit=${limit}&sort_by=${sortBy}`;
  if (style) url += `&style=${style}`;
  return fetchAPI<LeaderboardEntry[]>(url);
}

export function getWalletScore(address: string) {
  return fetchAPI<WalletScore>(`/api/wallet/${address}/score`);
}

export function getWalletFills(address: string, limit = 100) {
  return fetchAPI<WalletFill[]>(`/api/wallet/${address}/fills?limit=${limit}`);
}

export function getWalletSnapshot(address: string) {
  return fetchAPI<WalletSnapshot>(`/api/wallet/${address}/snapshot`);
}

export function getWalletHistory(address: string, limit = 30) {
  return fetchAPI<ScoreHistoryPoint[]>(
    `/api/wallet/${address}/history?limit=${limit}`
  );
}

export function submitWallet(address: string, label?: string) {
  return fetchAPI<{ address: string; status: string }>(
    "/api/wallet",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, label }),
    }
  );
}
