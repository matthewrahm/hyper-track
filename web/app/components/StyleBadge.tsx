import { styleLabel, styleColor } from "@/lib/utils";

export default function StyleBadge({ style }: { style: string | null }) {
  if (!style) return null;

  const color = styleColor(style);

  return (
    <span
      className="text-xs font-medium px-2 py-0.5 rounded-md"
      style={{
        color,
        background: `${color}18`,
      }}
    >
      {styleLabel(style)}
    </span>
  );
}
