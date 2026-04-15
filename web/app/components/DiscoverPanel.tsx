"use client";

import { useState } from "react";
import { Radar, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003";

interface DiscoverResult {
  added: number;
  scanned: number;
  total_candidates: number;
  message: string;
}

export default function DiscoverPanel({
  onDiscovered,
}: {
  onDiscovered?: () => void;
}) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<DiscoverResult | null>(null);
  const [error, setError] = useState("");

  const runDiscovery = async () => {
    setRunning(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/discover/vaults`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data: DiscoverResult = await res.json();
      setResult(data);
      if (data.added > 0) onDiscovered?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Discovery failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="card p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="label">Wallet Discovery</div>
          <p className="text-xs text-muted mt-1">
            Scan Hyperliquid vault followers to find active perp traders
          </p>
        </div>
        <button
          onClick={runDiscovery}
          disabled={running}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-xs font-medium text-white hover:opacity-85 disabled:opacity-50 transition-opacity"
        >
          {running ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Radar size={14} />
          )}
          {running ? "Scanning..." : "Scan HLP Vault"}
        </button>
      </div>

      {running && (
        <div className="rounded-lg bg-white/[0.02] p-3">
          <p className="text-xs text-secondary">
            Checking vault followers for trading activity. This queries up to
            100 addresses and takes 30-60 seconds...
          </p>
        </div>
      )}

      {result && (
        <div className="rounded-lg bg-white/[0.02] p-3">
          <div className="flex items-center gap-6">
            <div>
              <span className="num text-lg font-semibold text-profit">
                {result.added}
              </span>
              <span className="text-xs text-muted ml-1">new wallets</span>
            </div>
            <div>
              <span className="num text-lg font-semibold text-secondary">
                {result.scanned}
              </span>
              <span className="text-xs text-muted ml-1">scanned</span>
            </div>
            <div>
              <span className="num text-lg font-semibold text-secondary">
                {result.total_candidates}
              </span>
              <span className="text-xs text-muted ml-1">candidates</span>
            </div>
          </div>
          <p className="text-xs text-muted mt-2">{result.message}</p>
          {result.added > 0 && (
            <p className="text-xs text-secondary mt-1">
              New wallets will appear on the leaderboard after backfill and scoring completes.
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-loss/10 p-3">
          <p className="text-xs text-loss">{error}</p>
        </div>
      )}

      <div className="mt-3 text-[11px] text-muted leading-relaxed">
        <strong className="text-secondary">How it works:</strong> Queries the
        HLP vault (Hyperliquid&apos;s main market-making vault) for depositor
        addresses, then checks each for perp trading activity in the last 90
        days. Addresses with 10+ fills are added as tracked wallets.
      </div>
    </section>
  );
}
