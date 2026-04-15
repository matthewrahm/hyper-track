"use client";

import { useCallback, useState } from "react";
import { getLeaderboard, type LeaderboardEntry } from "@/lib/api";
import { useAutoRefresh } from "@/app/hooks/useAutoRefresh";
import { formatSignedCurrency } from "@/lib/utils";
import AddressCell from "./AddressCell";
import ScoreBadge from "./ScoreBadge";
import StyleBadge from "./StyleBadge";
import NumberCell from "./NumberCell";
import SubmitWallet from "./SubmitWallet";
import InfoTerm from "./InfoTerm";
import { GLOSSARY } from "@/lib/glossary";

type SortKey = keyof LeaderboardEntry;

const STYLES = ["all", "scalper", "day_trader", "swing_trader", "position_trader"];
const STYLE_LABELS: Record<string, string> = {
  all: "All",
  scalper: "Scalper",
  day_trader: "Day Trader",
  swing_trader: "Swing",
  position_trader: "Position",
};

export default function LeaderboardTable() {
  const [sortBy, setSortBy] = useState<SortKey>("composite_score");
  const [sortDesc, setSortDesc] = useState(true);
  const [styleFilter, setStyleFilter] = useState("all");

  const fetchLeaderboard = useCallback(
    () => getLeaderboard(100, "composite_score", styleFilter === "all" ? undefined : styleFilter),
    [styleFilter]
  );
  const { data, loading, refresh } = useAutoRefresh(fetchLeaderboard, 30_000);

  const handleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(key);
      setSortDesc(true);
    }
  };

  const sorted = data
    ? [...data].sort((a, b) => {
        const av = (a[sortBy] ?? 0) as number;
        const bv = (b[sortBy] ?? 0) as number;
        return sortDesc ? bv - av : av - bv;
      })
    : [];

  const SortHeader = ({
    label,
    field,
    align = "right",
  }: {
    label: string;
    field: SortKey;
    align?: "left" | "right";
  }) => (
    <th
      className={`table-header cursor-pointer select-none transition-colors hover:text-primary ${
        align === "right" ? "text-right" : "text-left"
      } ${sortBy === field ? "text-primary" : ""}`}
      onClick={() => handleSort(field)}
    >
      {label}
    </th>
  );

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="label">Top Traders</div>
          <div className="flex items-center gap-1">
            {STYLES.map((s) => (
              <button
                key={s}
                onClick={() => setStyleFilter(s)}
                className={`px-2.5 py-1 rounded-md text-xs transition-colors ${
                  styleFilter === s
                    ? "bg-elevated text-primary"
                    : "text-muted hover:text-secondary"
                }`}
              >
                {STYLE_LABELS[s]}
              </button>
            ))}
          </div>
        </div>
        <SubmitWallet onSubmitted={refresh} />
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="skeleton h-10 w-full" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted">
          No wallets tracked yet. Submit an address to get started.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header text-left w-8">#</th>
                <th className="table-header text-left">Wallet</th>
                <th className="table-header text-left">
                  <InfoTerm label="Style" explanation={GLOSSARY["Style"]} side="bottom" />
                </th>
                <SortHeader label="Score" field="composite_score" />
                <SortHeader label="PnL (90d)" field="pnl_90d" />
                <SortHeader label="ROI" field="roi_90d" />
                <SortHeader label="Win %" field="win_rate_90d" />
                <SortHeader label="Sharpe" field="sharpe_90d" />
                <th className="table-header text-right hidden lg:table-cell">
                  <InfoTerm label="Sortino" explanation={GLOSSARY["Sortino"]} side="bottom" />
                </th>
                <th className="table-header text-right hidden lg:table-cell">
                  <InfoTerm label="Max DD" explanation={GLOSSARY["Max Drawdown"]} side="bottom" />
                </th>
                <SortHeader label="Trades" field="trades_90d" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((w, i) => (
                <tr key={w.address} className="table-row">
                  <td className="table-cell text-muted text-xs">{i + 1}</td>
                  <td className="table-cell">
                    <AddressCell address={w.address} />
                  </td>
                  <td className="table-cell">
                    <StyleBadge style={w.style} />
                  </td>
                  <td className="table-cell text-right">
                    <ScoreBadge score={w.composite_score} />
                  </td>
                  <td className="table-cell text-right">
                    <span
                      className={`num font-medium ${
                        (w.pnl_90d ?? 0) >= 0 ? "text-profit" : "text-loss"
                      }`}
                    >
                      {formatSignedCurrency(w.pnl_90d ?? 0)}
                    </span>
                  </td>
                  <td className="table-cell text-right">
                    <NumberCell
                      value={(w.roi_90d ?? 0) * 100}
                      format="pct"
                      colorize
                    />
                  </td>
                  <td className="table-cell text-right">
                    <span className="num text-secondary">
                      {((w.win_rate_90d ?? 0) * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="table-cell text-right">
                    <span className="num text-secondary">
                      {(w.sharpe_90d ?? 0).toFixed(2)}
                    </span>
                  </td>
                  <td className="table-cell text-right hidden lg:table-cell">
                    <span className="num text-secondary">
                      {(w.sortino_90d ?? 0).toFixed(2)}
                    </span>
                  </td>
                  <td className="table-cell text-right hidden lg:table-cell">
                    <span className="num text-loss">
                      {((w.max_drawdown_90d ?? 0) * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="table-cell text-right">
                    <span className="num text-secondary">
                      {w.trades_90d ?? 0}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
