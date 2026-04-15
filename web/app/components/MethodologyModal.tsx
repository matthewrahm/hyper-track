"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { X, BookOpen } from "lucide-react";
import {
  SCORE_WEIGHTS,
  STYLE_EXPLANATIONS,
  TAG_EXPLANATIONS,
} from "@/lib/glossary";
import { styleLabel, styleColor } from "@/lib/utils";

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.min(value * 100, 100)}%`, background: color }}
      />
    </div>
  );
}

export default function MethodologyModal() {
  const [open, setOpen] = useState(false);

  const content = (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />
      <div
        className="relative card p-8 max-w-2xl w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-primary">
            How Scoring Works
          </h2>
          <button
            onClick={() => setOpen(false)}
            className="text-muted hover:text-primary transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Composite Score */}
        <section className="mb-8">
          <h3 className="text-sm font-semibold text-primary mb-2">
            Composite Score (0-100)
          </h3>
          <p className="text-xs text-secondary mb-4 leading-relaxed">
            Every tracked wallet receives a composite score combining 9
            risk-adjusted performance metrics. Each metric is normalized to a
            0-1 range with sensible caps, then weighted. The 90-day window is
            the primary scoring period.
          </p>
          <div className="space-y-3">
            {SCORE_WEIGHTS.map((w) => (
              <div key={w.key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-primary">
                    {w.label}
                  </span>
                  <span className="num text-xs text-muted">
                    {(w.weight * 100).toFixed(0)}%
                  </span>
                </div>
                <ProgressBar value={w.weight / 0.15} color="#6366f1" />
                <p className="text-[11px] text-muted mt-1">{w.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Metric Definitions */}
        <section className="mb-8">
          <h3 className="text-sm font-semibold text-primary mb-2">
            Key Metrics
          </h3>
          <div className="space-y-3">
            <div className="rounded-lg bg-white/[0.02] p-3">
              <span className="text-xs font-medium text-primary">
                Sharpe Ratio
              </span>
              <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                Annualized risk-adjusted return. Calculated from daily PnL
                buckets: mean daily return divided by standard deviation, times
                sqrt(365). Above 2.0 is strong. Above 3.0 is exceptional. A
                negative Sharpe means the wallet is losing money on a
                risk-adjusted basis.
              </p>
            </div>
            <div className="rounded-lg bg-white/[0.02] p-3">
              <span className="text-xs font-medium text-primary">
                Sortino Ratio
              </span>
              <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                Like Sharpe but only penalizes downside volatility. Upside
                variance is ignored. Better for evaluating traders with
                asymmetric returns (big wins, controlled losses). Calculated
                using downside deviation of daily returns.
              </p>
            </div>
            <div className="rounded-lg bg-white/[0.02] p-3">
              <span className="text-xs font-medium text-primary">
                Profit Factor
              </span>
              <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                Total gross profits divided by total gross losses. A profit
                factor of 2.0 means you earn $2 for every $1 you lose. Above
                1.5 is good, above 2.0 is strong. Below 1.0 means the wallet is
                a net loser.
              </p>
            </div>
            <div className="rounded-lg bg-white/[0.02] p-3">
              <span className="text-xs font-medium text-primary">
                Max Drawdown
              </span>
              <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                The largest peak-to-trough decline in cumulative PnL. Measures
                the worst-case loss from a high point. A 20% max drawdown means
                PnL fell 20% from its peak before recovering. Lower is better
                and weighted heavily in the composite.
              </p>
            </div>
            <div className="rounded-lg bg-white/[0.02] p-3">
              <span className="text-xs font-medium text-primary">
                Round-Trip Trades
              </span>
              <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                Fills are grouped into round-trip trades by coin. A trade opens
                when position goes from zero to non-zero and closes when it
                returns to zero. Partial closes and position reversals are
                tracked. PnL is computed from the closed_pnl field minus fees.
              </p>
            </div>
          </div>
        </section>

        {/* Time Windows */}
        <section className="mb-8">
          <h3 className="text-sm font-semibold text-primary mb-2">
            Time Windows
          </h3>
          <p className="text-xs text-secondary mb-3 leading-relaxed">
            Every metric is calculated across three rolling windows. The 90-day
            window drives the composite score and leaderboard ranking.
          </p>
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-white/[0.02] p-3 text-center">
              <div className="text-sm font-semibold text-primary">30 Day</div>
              <p className="text-[11px] text-muted mt-1">Recent performance</p>
            </div>
            <div className="rounded-lg bg-accent/10 border border-accent/20 p-3 text-center">
              <div className="text-sm font-semibold text-accent">90 Day</div>
              <p className="text-[11px] text-muted mt-1">
                Primary scoring window
              </p>
            </div>
            <div className="rounded-lg bg-white/[0.02] p-3 text-center">
              <div className="text-sm font-semibold text-primary">All Time</div>
              <p className="text-[11px] text-muted mt-1">Full history</p>
            </div>
          </div>
        </section>

        {/* Style Classification */}
        <section className="mb-8">
          <h3 className="text-sm font-semibold text-primary mb-2">
            Style Classification
          </h3>
          <p className="text-xs text-secondary mb-4 leading-relaxed">
            Each wallet is classified by trading style based on two dimensions:
            average hold time and trade frequency from the 90-day window.
          </p>
          <div className="space-y-3">
            {Object.entries(STYLE_EXPLANATIONS).map(([key, desc]) => (
              <div key={key} className="flex gap-3 items-start">
                <span
                  className="text-xs font-medium px-2 py-0.5 rounded-md shrink-0 mt-0.5"
                  style={{
                    color: styleColor(key),
                    background: `${styleColor(key)}18`,
                  }}
                >
                  {styleLabel(key)}
                </span>
                <p className="text-[11px] text-secondary leading-relaxed">
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Style Tags */}
        <section>
          <h3 className="text-sm font-semibold text-primary mb-2">
            Style Tags
          </h3>
          <p className="text-xs text-secondary mb-4 leading-relaxed">
            Additional behavioral tags that can be assigned alongside the
            primary style. A wallet can have multiple tags.
          </p>
          <div className="space-y-3">
            {Object.entries(TAG_EXPLANATIONS).map(([key, desc]) => (
              <div key={key} className="flex gap-3 items-start">
                <span className="text-xs font-medium text-muted px-2 py-0.5 rounded-md bg-white/[0.04] shrink-0 mt-0.5">
                  {key}
                </span>
                <p className="text-[11px] text-secondary leading-relaxed">
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-xs text-secondary hover:text-primary transition-colors"
      >
        <BookOpen size={14} />
        Methodology
      </button>
      {open && typeof window !== "undefined" && createPortal(content, document.body)}
    </>
  );
}
