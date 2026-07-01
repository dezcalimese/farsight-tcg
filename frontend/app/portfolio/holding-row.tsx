"use client";

import type { Holding } from "@/lib/api";
import { PokeballPlaceholder } from "../motif-icon";

export function HoldingRow({ holding, onDelete }: { holding: Holding; onDelete: () => void }) {
  const gain = holding.pnl !== null && holding.pnl >= 0;

  return (
    <div className="glass-panel-row flex items-center gap-3 px-4 py-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-white/70 bg-white/50 text-ink/50">
        {holding.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={holding.image_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <PokeballPlaceholder className="h-5 w-5" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm text-ink">{holding.item_name}</div>
        <div className="text-xs text-muted">
          {holding.quantity} &times; ${holding.purchase_price.toFixed(2)}
        </div>
      </div>
      <div className="shrink-0 text-right">
        {holding.market_value !== null ? (
          <>
            <div className="font-mono text-sm text-ink">${holding.market_value.toFixed(2)}</div>
            <div className={`font-mono text-xs ${gain ? "text-gain" : "text-loss"}`}>
              {gain ? "+" : ""}
              {holding.pnl?.toFixed(2)} ({gain ? "+" : ""}
              {holding.pnl_pct?.toFixed(1)}%)
            </div>
          </>
        ) : (
          <div className="text-xs text-muted">no price data</div>
        )}
      </div>
      <button
        type="button"
        onClick={onDelete}
        aria-label="Remove holding"
        className="shrink-0 rounded-full px-2 py-1 text-xs text-muted hover:text-loss"
      >
        ✕
      </button>
    </div>
  );
}
