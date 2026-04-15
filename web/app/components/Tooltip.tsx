"use client";

import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  side?: "top" | "bottom";
}

export default function Tooltip({ content, children, side = "top" }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!visible || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setCoords({
      x: rect.left + rect.width / 2,
      y: side === "top" ? rect.top - 8 : rect.bottom + 8,
    });
  }, [visible, side]);

  return (
    <>
      <span
        ref={triggerRef}
        className="relative inline-flex"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
      >
        {children}
      </span>
      {visible &&
        typeof window !== "undefined" &&
        createPortal(
          <div
            className="fixed z-[100] pointer-events-none"
            style={{
              left: coords.x,
              top: coords.y,
              transform:
                side === "top"
                  ? "translate(-50%, -100%)"
                  : "translate(-50%, 0)",
            }}
          >
            <div className="w-max max-w-[260px] px-3 py-2 bg-elevated border border-white/10 rounded-md text-xs text-secondary leading-relaxed shadow-[0_4px_24px_rgba(0,0,0,0.5)]">
              {content}
            </div>
          </div>,
          document.body
        )}
    </>
  );
}
