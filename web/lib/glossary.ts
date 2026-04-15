export const GLOSSARY: Record<string, string> = {
  "Composite Score":
    "Overall wallet rating (0-100) combining ROI, Sharpe, drawdown, profit factor, win rate, Sortino, R:R, trade volume, and longevity. Higher is better.",
  "PnL 90d":
    "Total realized profit or loss from closed trades in the last 90 days, after fees.",
  ROI: "Return on investment. Total PnL divided by the time-weighted average capital deployed.",
  "Win Rate":
    "Percentage of round-trip trades that were profitable. A trade opens when a position goes from 0 to non-zero and closes when it returns to 0.",
  Sharpe:
    "Annualized Sharpe ratio. Measures return per unit of risk using daily PnL volatility. Above 2.0 is strong, above 3.0 is exceptional.",
  Sortino:
    "Like Sharpe but only penalizes downside volatility. Better for traders with asymmetric returns (big wins, small losses).",
  "Max Drawdown":
    "Largest peak-to-trough decline in cumulative PnL. A 20% drawdown means PnL dropped 20% from its highest point before recovering.",
  "Profit Factor":
    "Gross profits divided by gross losses. Above 2.0 means you make $2 for every $1 lost. Below 1.0 means net losing.",
  "Reward:Risk":
    "Average winning trade size divided by average losing trade size. A 3:1 R:R means winners are 3x larger than losers on average.",
  Trades: "Number of completed round-trip trades in the time window.",
  "Avg Hold":
    "Average time a position is held from open to close. Short hold times suggest scalping, longer holds suggest swing or position trading.",
  Style:
    "Trading style classified by average hold time and trade frequency. Scalper (<1h, >10/day), Day Trader (<24h, >2/day), Swing (<7d), Position (>7d).",
};

export const STYLE_EXPLANATIONS: Record<string, string> = {
  scalper:
    "Opens and closes positions within minutes. High trade frequency (10+/day), very short hold times (<1 hour). Profits from small price movements and tight spreads.",
  day_trader:
    "Completes trades within a single day. Moderate frequency (2-10/day), holds for hours. Captures intraday momentum and reversals.",
  swing_trader:
    "Holds positions for days to a week. Lower frequency, lets trades develop. Captures medium-term trends and price swings between support/resistance.",
  position_trader:
    "Holds positions for weeks or longer. Very selective, few trades. Captures major market moves and macro trends with conviction sizing.",
};

export const TAG_EXPLANATIONS: Record<string, string> = {
  degen:
    "Extremely high frequency with very short holds. Aggressive style often using high leverage on volatile assets.",
  sniper:
    "High accuracy (70%+ win rate) with fast execution (<2h holds). Precisely times entries and exits.",
  grinder:
    "Very high trade volume (20+/day) with moderate win rate (45-55%). Relies on volume and small edges that compound.",
  concentrated:
    "Over 80% of trading volume in a single asset. Deep specialization in one market.",
  diversified:
    "Trades 10+ different assets with no single one exceeding 30% of volume. Spreads risk across markets.",
};

export const SCORE_WEIGHTS = [
  { key: "roi", label: "ROI", weight: 0.15, description: "Return on time-weighted average capital. Capped at 500%." },
  { key: "sharpe", label: "Sharpe Ratio", weight: 0.15, description: "Risk-adjusted return using daily PnL volatility. Capped at 5.0." },
  { key: "drawdown", label: "Max Drawdown", weight: 0.15, description: "Inverted -- lower drawdown scores higher. 0% drawdown = perfect score." },
  { key: "win_rate", label: "Win Rate", weight: 0.10, description: "Percentage of profitable trades. Raw value, not capped." },
  { key: "sortino", label: "Sortino Ratio", weight: 0.10, description: "Downside-only risk adjustment. Capped at 8.0." },
  { key: "profit_factor", label: "Profit Factor", weight: 0.10, description: "Gross profit / gross loss. Capped at 5.0." },
  { key: "volume", label: "Trade Volume", weight: 0.10, description: "Number of completed trades. 200+ trades = full score." },
  { key: "longevity", label: "Longevity", weight: 0.10, description: "Days active on the platform. 180+ days = full score." },
  { key: "reward_risk", label: "Reward:Risk", weight: 0.05, description: "Average win size / average loss size. Capped at 5.0." },
];
