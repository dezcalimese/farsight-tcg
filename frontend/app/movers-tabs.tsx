"use client";

import { useState } from "react";
import type { Period, PriceMove } from "@/lib/api";
import { MoveRow } from "./move-row";

export function MoversTabs({ moves, period }: { moves: PriceMove[]; period: Period }) {
  const [category, setCategory] = useState<"card" | "sealed_product">("card");

  const cards = moves.filter((m) => m.item_type === "card");
  const packs = moves.filter((m) => m.item_type === "sealed_product");
  const shown = category === "card" ? cards : packs;

  return (
    <div>
      <div className="mb-2.5 flex gap-2">
        <button
          type="button"
          data-active={category === "card"}
          onClick={() => setCategory("card")}
          className="glass-btn px-3.5 py-1.5 text-xs font-medium"
        >
          Cards ({cards.length})
        </button>
        <button
          type="button"
          data-active={category === "sealed_product"}
          onClick={() => setCategory("sealed_product")}
          className="glass-btn px-3.5 py-1.5 text-xs font-medium"
        >
          Packs ({packs.length})
        </button>
      </div>
      <div className="glass-panel overflow-hidden">
        {shown.length === 0 ? (
          <div className="px-4 py-3 text-sm text-muted">
            No {category === "card" ? "card" : "pack"} moves this period.
          </div>
        ) : (
          shown.map((m) => <MoveRow key={m.item_id} move={m} period={period} />)
        )}
      </div>
    </div>
  );
}
