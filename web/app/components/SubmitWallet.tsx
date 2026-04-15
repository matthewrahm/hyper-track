"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { submitWallet } from "@/lib/api";

const ADDRESS_RE = /^0x[0-9a-fA-F]{40}$/;

export default function SubmitWallet({ onSubmitted }: { onSubmitted?: () => void }) {
  const [open, setOpen] = useState(false);
  const [address, setAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    const trimmed = address.trim();
    if (!ADDRESS_RE.test(trimmed)) {
      setError("Invalid address");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await submitWallet(trimmed);
      setAddress("");
      setOpen(false);
      onSubmitted?.();
    } catch {
      setError("Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-xs text-secondary hover:text-primary transition-colors"
      >
        <Plus size={14} />
        Track Wallet
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="0x..."
        className="h-8 w-80 rounded-lg bg-elevated px-3 text-xs font-mono text-primary placeholder:text-muted outline-none"
        style={{ border: "1px solid rgba(255,255,255,0.10)" }}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        autoFocus
      />
      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="h-8 rounded-lg bg-accent px-3 text-xs font-medium text-white hover:opacity-85 disabled:opacity-50"
      >
        {submitting ? "..." : "Track"}
      </button>
      <button
        onClick={() => { setOpen(false); setError(""); }}
        className="text-xs text-muted hover:text-primary"
      >
        Cancel
      </button>
      {error && <span className="text-xs text-loss">{error}</span>}
    </div>
  );
}
