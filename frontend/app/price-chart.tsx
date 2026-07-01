"use client";

import { Liveline } from "liveline";
import { useEffect, useState } from "react";
import type { Period, PriceHistoryPoint } from "@/lib/api";
import { getPriceHistory } from "@/lib/api";

const PERIOD_DAYS: Record<Period, number> = { daily: 1, weekly: 7 };

export function PriceChart({
  itemType,
  itemId,
  period,
}: {
  itemType: "card" | "sealed_product";
  itemId: string;
  period: Period;
}) {
  const [data, setData] = useState<PriceHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [accentColor, setAccentColor] = useState("#8b5cf6");

  useEffect(() => {
    const value = getComputedStyle(document.documentElement).getPropertyValue("--accent-1").trim();
    if (value) setAccentColor(value);
  }, [period]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getPriceHistory(itemType, itemId, PERIOD_DAYS[period])
      .then((points) => {
        if (!cancelled) setData(points);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [itemType, itemId, period]);

  const latest = data.at(-1)?.value ?? 0;
  const windowSecs = PERIOD_DAYS[period] * 86400;

  return (
    <div className="border-t border-white/50 bg-white/30 px-3 py-3" style={{ height: 170 }}>
      <Liveline
        data={data}
        value={latest}
        color={accentColor}
        theme="light"
        grid
        badge
        scrub
        pulse={false}
        loading={loading}
        emptyText="Not enough price history yet"
        window={windowSecs}
        formatValue={(v: number) => `$${v.toFixed(2)}`}
        formatTime={(t: number) => new Date(t * 1000).toLocaleDateString()}
      />
    </div>
  );
}
