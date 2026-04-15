"use client";

import Link from "next/link";
import { Copy } from "lucide-react";
import { useState } from "react";

export default function AddressCell({ address }: { address: string }) {
  const [copied, setCopied] = useState(false);
  const short = `${address.slice(0, 6)}...${address.slice(-4)}`;

  const handleCopy = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="flex items-center gap-2">
      <Link
        href={`/wallet/${address}`}
        className="num text-sm text-accent hover:text-accent-hover transition-colors"
      >
        {short}
      </Link>
      <button
        onClick={handleCopy}
        className="text-muted hover:text-primary transition-colors"
        title="Copy address"
      >
        {copied ? (
          <span className="text-xs text-profit">Copied</span>
        ) : (
          <Copy size={12} />
        )}
      </button>
    </div>
  );
}
