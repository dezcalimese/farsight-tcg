"use client";

import { useState } from "react";
import type { Period, PriceMove } from "@/lib/api";
import { PokeballPlaceholder } from "./motif-icon";
import { PriceChart } from "./price-chart";

export function MoveRow({
  move,
  period,
  showType = false,
}: {
  move: PriceMove;
  period: Period;
  showType?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const positive = move.pct_change >= 0;

  return (
    <div className="glass-panel-row">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-white/40"
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-white/70 bg-white/50 text-ink/50">
          {move.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={move.image_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <PokeballPlaceholder className="h-5 w-5" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm text-ink">
            {move.item_name}
            {showType && (
              <span className="ml-1.5 text-xs text-muted">({move.item_type.replace("_", " ")})</span>
            )}
          </div>
          <div className={`font-mono text-[13px] ${positive ? "text-gain" : "text-loss"}`}>
            {positive ? "+" : ""}
            {move.pct_change.toFixed(1)}% &middot; ${move.price_then.toFixed(2)} &rarr; $
            {move.price_now.toFixed(2)}
          </div>
        </div>
        <span className="shrink-0 text-xs text-muted">{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && <PriceChart itemType={move.item_type} itemId={move.item_id} period={period} />}
    </div>
  );
}
