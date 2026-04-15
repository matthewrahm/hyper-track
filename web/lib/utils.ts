import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(value: number): string {
  const sign = value >= 0 ? "" : "-";
  return `${sign}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatSignedCurrency(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${sign}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatCompact(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return formatCurrency(value);
}

export function formatPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function rateColor(value: number): string {
  if (value > 0) return "text-profit";
  if (value < 0) return "text-loss";
  return "text-secondary";
}

export function truncateAddress(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function styleLabel(style: string): string {
  const labels: Record<string, string> = {
    scalper: "Scalper",
    day_trader: "Day Trader",
    swing_trader: "Swing Trader",
    position_trader: "Position Trader",
  };
  return labels[style] || style;
}

export function styleColor(style: string): string {
  const colors: Record<string, string> = {
    scalper: "#f472b6",
    day_trader: "#60a5fa",
    swing_trader: "#a78bfa",
    position_trader: "#34d399",
  };
  return colors[style] || "#a1a1aa";
}
