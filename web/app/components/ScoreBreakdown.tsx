"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { SCORE_WEIGHTS } from "@/lib/glossary";
import type { WalletScore } from "@/lib/api";

function clamp(value: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, value));
}

function getBarColor(normalized: number): string {
  if (normalized >= 0.7) return "#22c55e";
  if (normalized >= 0.4) return "#f59e0b";
  return "#ef4444";
}

function computeFactors(score: WalletScore) {
  const roi = score.roi_90d ?? 0;
  const wr = score.win_rate_90d ?? 0;
  const sharpe = score.sharpe_90d ?? 0;
  const sortino = score.sortino_90d ?? 0;
  const dd = score.max_drawdown_90d ?? 0;
  const pf = score.profit_factor_90d ?? 0;
  const rr = score.reward_risk_90d ?? 0;
  const trades = score.trades_90d ?? 0;
  const days = score.active_days ?? 0;

  return [
    {
      label: "ROI",
      raw: `${(roi * 100).toFixed(1)}%`,
      normalized: clamp(roi, -1, 5) / 5,
      weight: 0.15,
      description: "Return on time-weighted capital (capped at 500%)",
    },
    {
      label: "Sharpe Ratio",
      raw: sharpe.toFixed(2),
      normalized: clamp(sharpe, -2, 5) / 5,
      weight: 0.15,
      description: "Annualized risk-adjusted return (capped at 5.0)",
    },
    {
      label: "Max Drawdown",
      raw: `${(dd * 100).toFixed(1)}%`,
      normalized: 1 - clamp(dd, 0, 1),
      weight: 0.15,
      description: "Inverted: lower drawdown scores higher",
    },
    {
      label: "Win Rate",
      raw: `${(wr * 100).toFixed(1)}%`,
      normalized: wr,
      weight: 0.10,
      description: "Percentage of profitable round-trip trades",
    },
    {
      label: "Sortino Ratio",
      raw: sortino.toFixed(2),
      normalized: clamp(sortino, -2, 8) / 8,
      weight: 0.10,
      description: "Downside risk-adjusted return (capped at 8.0)",
    },
    {
      label: "Profit Factor",
      raw: pf.toFixed(2),
      normalized: clamp(pf, 0, 5) / 5,
      weight: 0.10,
      description: "Gross profit / gross loss (capped at 5.0)",
    },
    {
      label: "Trade Volume",
      raw: `${trades} trades`,
      normalized: clamp(trades / 200, 0, 1),
      weight: 0.10,
      description: "Number of completed trades (200+ = full score)",
    },
    {
      label: "Longevity",
      raw: `${days} days`,
      normalized: clamp(days / 180, 0, 1),
      weight: 0.10,
      description: "Days active on the platform (180+ = full score)",
    },
    {
      label: "Reward:Risk",
      raw: `${rr.toFixed(2)}:1`,
      normalized: clamp(rr, 0, 5) / 5,
      weight: 0.05,
      description: "Average win / average loss size (capped at 5.0)",
    },
  ];
}

export default function ScoreBreakdown({ score }: { score: WalletScore }) {
  const [open, setOpen] = useState(false);
  const factors = computeFactors(score);

  const content = (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />
      <div
        className="relative card p-8 max-w-md w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-semibold text-primary">
            Score Breakdown
          </h3>
          <button
            onClick={() => setOpen(false)}
            className="text-muted hover:text-primary transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-white/10">
          <span className="num text-3xl font-bold text-primary">
            {score.composite_score.toFixed(1)}
          </span>
          <p className="text-xs text-secondary leading-relaxed">
            Composite score from 9 weighted metrics over the 90-day window.
            Click any factor below to understand how it contributes.
          </p>
        </div>

        <div className="space-y-4">
          {factors.map((f) => {
            const contribution = f.normalized * f.weight * 100;
            return (
              <div key={f.label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-primary">
                    {f.label}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="num text-xs text-secondary">{f.raw}</span>
                    <span className="num text-xs text-muted">
                      +{contribution.toFixed(1)}pts
                    </span>
                  </div>
                </div>
                <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.max(f.normalized * 100, 0)}%`,
                      background: getBarColor(f.normalized),
                    }}
                  />
                </div>
                <p className="text-[11px] text-muted mt-1">{f.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <button onClick={() => setOpen(true)} className="cursor-pointer">
        <span
          className="num text-sm font-semibold px-2 py-0.5 rounded-md hover:opacity-80 transition-opacity"
          style={{
            color:
              score.composite_score >= 70
                ? "#22c55e"
                : score.composite_score >= 40
                  ? "#FFD166"
                  : "#ef4444",
            background:
              score.composite_score >= 70
                ? "rgba(34, 197, 94, 0.12)"
                : score.composite_score >= 40
                  ? "rgba(255, 209, 102, 0.12)"
                  : "rgba(239, 68, 68, 0.12)",
          }}
        >
          {score.composite_score.toFixed(1)}
        </span>
      </button>
      {open &&
        typeof window !== "undefined" &&
        createPortal(content, document.body)}
    </>
  );
}
