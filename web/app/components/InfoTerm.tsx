"use client";

import { Info } from "lucide-react";
import Tooltip from "./Tooltip";

export default function InfoTerm({
  label,
  explanation,
  side = "top",
}: {
  label: string;
  explanation: string;
  side?: "top" | "bottom";
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {label}
      <Tooltip content={explanation} side={side}>
        <Info size={11} className="text-muted cursor-help" />
      </Tooltip>
    </span>
  );
}
