"use client";

import { useCallback, use } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import {
  getWalletScore,
  getWalletSnapshot,
  getWalletFills,
  type WalletScore,
  type WalletSnapshot,
  type WalletFill,
} from "@/lib/api";
import { useAutoRefresh } from "@/app/hooks/useAutoRefresh";
import { formatCurrency, formatSignedCurrency, truncateAddress, styleLabel } from "@/lib/utils";
import ScoreBadge from "@/app/components/ScoreBadge";
import ScoreBreakdown from "@/app/components/ScoreBreakdown";
import StyleBadge from "@/app/components/StyleBadge";
import NumberCell from "@/app/components/NumberCell";
import InfoTerm from "@/app/components/InfoTerm";
import { GLOSSARY } from "@/lib/glossary";

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="card p-4">
      <div className="label mb-2">{label}</div>
      <div className="num text-lg font-semibold text-primary">{value}</div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </div>
  );
}

function WindowTable({ score, window }: { score: WalletScore; window: "30d" | "90d" | "all" }) {
  const suffix = `_${window}` as const;
  const get = (key: string) => (score as unknown as Record<string, unknown>)[`${key}${suffix}`] as number | null;

  return (
    <div className="grid grid-cols-2 gap-x-8 gap-y-3">
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="PnL" explanation={GLOSSARY["PnL 90d"]} />
        </span>
        <div className={`num text-sm font-medium ${(get("pnl") ?? 0) >= 0 ? "text-profit" : "text-loss"}`}>
          {formatSignedCurrency(get("pnl") ?? 0)}
        </div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="ROI" explanation={GLOSSARY["ROI"]} />
        </span>
        <div className="num text-sm">
          <NumberCell value={(get("roi") ?? 0) * 100} format="pct" colorize />
        </div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Win Rate" explanation={GLOSSARY["Win Rate"]} />
        </span>
        <div className="num text-sm text-secondary">
          {((get("win_rate") ?? 0) * 100).toFixed(1)}%
        </div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Trades" explanation={GLOSSARY["Trades"]} />
        </span>
        <div className="num text-sm text-secondary">{get("trades") ?? 0}</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Sharpe" explanation={GLOSSARY["Sharpe"]} />
        </span>
        <div className="num text-sm text-secondary">{(get("sharpe") ?? 0).toFixed(2)}</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Sortino" explanation={GLOSSARY["Sortino"]} />
        </span>
        <div className="num text-sm text-secondary">{(get("sortino") ?? 0).toFixed(2)}</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Max Drawdown" explanation={GLOSSARY["Max Drawdown"]} />
        </span>
        <div className="num text-sm text-loss">{((get("max_drawdown") ?? 0) * 100).toFixed(1)}%</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Profit Factor" explanation={GLOSSARY["Profit Factor"]} />
        </span>
        <div className="num text-sm text-secondary">{(get("profit_factor") ?? 0).toFixed(2)}</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="Avg Hold" explanation={GLOSSARY["Avg Hold"]} />
        </span>
        <div className="num text-sm text-secondary">{(get("avg_hold_hours") ?? 0).toFixed(1)}h</div>
      </div>
      <div>
        <span className="text-xs text-muted">
          <InfoTerm label="R:R" explanation={GLOSSARY["Reward:Risk"]} />
        </span>
        <div className="num text-sm text-secondary">{(get("reward_risk") ?? 0).toFixed(2)}</div>
      </div>
    </div>
  );
}

export default function WalletDetail({
  params,
}: {
  params: Promise<{ address: string }>;
}) {
  const { address } = use(params);

  const fetchScore = useCallback(() => getWalletScore(address), [address]);
  const fetchSnapshot = useCallback(() => getWalletSnapshot(address), [address]);
  const fetchFills = useCallback(() => getWalletFills(address, 50), [address]);

  const { data: score, loading: scoreLoading } = useAutoRefresh(fetchScore, 60_000);
  const { data: snapshot, loading: snapLoading } = useAutoRefresh(fetchSnapshot, 30_000);
  const { data: fills, loading: fillsLoading } = useAutoRefresh(fetchFills, 30_000);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="flex items-center gap-1.5 text-sm text-secondary hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft size={14} />
        Leaderboard
      </Link>

      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <h1 className="num text-xl font-semibold">{truncateAddress(address)}</h1>
        {score && <ScoreBreakdown score={score} />}
        {score && <StyleBadge style={score.style} />}
      </div>

      {scoreLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton h-20 w-full" />
          ))}
        </div>
      ) : score ? (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <MetricCard
              label="Account Value"
              value={formatCurrency(score.account_value ?? 0)}
            />
            <MetricCard
              label="90d PnL"
              value={formatSignedCurrency(score.pnl_90d ?? 0)}
            />
            <MetricCard
              label="Active Days"
              value={String(score.active_days ?? 0)}
            />
            <MetricCard
              label="Composite Score"
              value={score.composite_score.toFixed(1)}
            />
          </div>

          {/* Metric windows */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="card p-5">
              <div className="label mb-3">30 Day</div>
              <WindowTable score={score} window="30d" />
            </div>
            <div className="card p-5">
              <div className="label mb-3">90 Day</div>
              <WindowTable score={score} window="90d" />
            </div>
            <div className="card p-5">
              <div className="label mb-3">All Time</div>
              <WindowTable score={score} window="all" />
            </div>
          </div>
        </>
      ) : (
        <p className="text-muted py-8 text-center">No score data for this wallet.</p>
      )}

      {/* Positions */}
      <section className="card p-5 mb-6">
        <div className="label mb-3">Open Positions</div>
        {snapLoading ? (
          <div className="skeleton h-32 w-full" />
        ) : snapshot && snapshot.positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header text-left">Coin</th>
                  <th className="table-header text-left">Side</th>
                  <th className="table-header text-right">Size</th>
                  <th className="table-header text-right">Entry</th>
                  <th className="table-header text-right">Mark</th>
                  <th className="table-header text-right">uPnL</th>
                  <th className="table-header text-right">Leverage</th>
                  <th className="table-header text-right">Value</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.positions.map((p) => (
                  <tr key={p.coin} className="table-row">
                    <td className="table-cell font-medium text-primary">{p.coin}</td>
                    <td className="table-cell">
                      <span className={p.side === "LONG" ? "text-profit" : "text-loss"}>
                        {p.side}
                      </span>
                    </td>
                    <td className="table-cell text-right num">{p.size.toFixed(4)}</td>
                    <td className="table-cell text-right num">{formatCurrency(p.entry_price)}</td>
                    <td className="table-cell text-right num">{formatCurrency(p.mark_price)}</td>
                    <td className="table-cell text-right">
                      <NumberCell value={p.unrealized_pnl} format="currency" colorize />
                    </td>
                    <td className="table-cell text-right num">{p.leverage}x</td>
                    <td className="table-cell text-right num">{formatCurrency(p.position_value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted py-4 text-center">No open positions</p>
        )}
      </section>

      {/* Recent Fills */}
      <section className="card p-5">
        <div className="label mb-3">Recent Fills</div>
        {fillsLoading ? (
          <div className="skeleton h-48 w-full" />
        ) : fills && fills.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header text-left">Time</th>
                  <th className="table-header text-left">Coin</th>
                  <th className="table-header text-left">Direction</th>
                  <th className="table-header text-right">Price</th>
                  <th className="table-header text-right">Size</th>
                  <th className="table-header text-right">PnL</th>
                  <th className="table-header text-right">Fee</th>
                </tr>
              </thead>
              <tbody>
                {fills.map((f, i) => (
                  <tr key={`${f.time_ms}-${i}`} className="table-row">
                    <td className="table-cell text-xs text-muted">
                      {new Date(f.time_ms).toLocaleString()}
                    </td>
                    <td className="table-cell font-medium text-primary">{f.coin}</td>
                    <td className="table-cell">
                      <span
                        className={`text-xs ${
                          f.direction?.includes("Long") ? "text-profit" : "text-loss"
                        }`}
                      >
                        {f.direction || (f.side === "B" ? "Buy" : "Sell")}
                      </span>
                    </td>
                    <td className="table-cell text-right num">{formatCurrency(f.price)}</td>
                    <td className="table-cell text-right num">{f.size.toFixed(4)}</td>
                    <td className="table-cell text-right">
                      {f.closed_pnl !== 0 ? (
                        <NumberCell value={f.closed_pnl} format="currency" colorize />
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td className="table-cell text-right num text-muted">
                      {formatCurrency(f.fee)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted py-4 text-center">No fills recorded</p>
        )}
      </section>
    </div>
  );
}
