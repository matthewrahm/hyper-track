export default function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 70
      ? "text-profit"
      : score >= 40
        ? "text-[#FFD166]"
        : "text-loss";

  const bgColor =
    score >= 70
      ? "rgba(34, 197, 94, 0.12)"
      : score >= 40
        ? "rgba(255, 209, 102, 0.12)"
        : "rgba(239, 68, 68, 0.12)";

  return (
    <span
      className={`num text-sm font-semibold px-2 py-0.5 rounded-md ${color}`}
      style={{ background: bgColor }}
    >
      {score.toFixed(1)}
    </span>
  );
}
