import { cn } from "@/lib/utils";

type Format = "bps" | "pct" | "rate" | "currency";

function formatValue(value: number, format: Format): string {
  switch (format) {
    case "bps":
      return `${value.toFixed(1)}bp`;
    case "pct":
      return `${value.toFixed(1)}%`;
    case "rate": {
      const sign = value >= 0 ? "+" : "";
      return `${sign}${value.toFixed(4)}`;
    }
    case "currency": {
      const sign = value >= 0 ? "" : "-";
      return `${sign}$${Math.abs(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    }
  }
}

export default function NumberCell({
  value,
  format,
  colorize = false,
  className,
}: {
  value: number;
  format: Format;
  colorize?: boolean;
  className?: string;
}) {
  const color = colorize
    ? value > 0
      ? "text-profit"
      : value < 0
        ? "text-loss"
        : "text-secondary"
    : "text-secondary";

  return (
    <span className={cn("num text-right", color, className)}>
      {formatValue(value, format)}
    </span>
  );
}
