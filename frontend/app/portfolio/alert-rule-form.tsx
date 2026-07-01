"use client";

import { useEffect, useState } from "react";
import {
  createAlert,
  searchCatalog,
  type AlertRule,
  type AlertRuleType,
  type CatalogItem,
} from "@/lib/api";
import { PokeballPlaceholder } from "../motif-icon";

const RULE_LABELS: Record<AlertRuleType, string> = {
  price_above: "Price rises above",
  price_below: "Price drops below",
  pct_move: "% move within a window",
  restock: "Restock watch",
};

export function AlertRuleForm({
  token,
  onAdded,
}: {
  token: string;
  onAdded: (rule: AlertRule) => void;
}) {
  const [ruleType, setRuleType] = useState<AlertRuleType>("price_above");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CatalogItem[]>([]);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [threshold, setThreshold] = useState("");
  const [windowHours, setWindowHours] = useState("24");
  const [watchText, setWatchText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needsItem = ruleType !== "restock";

  useEffect(() => {
    if (selected || query.trim().length < 2) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      searchCatalog(query).then((items) => {
        if (!cancelled) setResults(items);
      });
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, selected]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const rule = await createAlert(token, {
        rule_type: ruleType,
        item_type: needsItem ? selected?.item_type : undefined,
        item_id: needsItem ? selected?.item_id : undefined,
        threshold: needsItem ? Number(threshold) : undefined,
        window_hours: ruleType === "pct_move" ? Number(windowHours) : undefined,
        watch_text: ruleType === "restock" ? watchText : undefined,
      });
      onAdded(rule);
      setSelected(null);
      setQuery("");
      setThreshold("");
      setWatchText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass-panel p-4">
      <h3 className="mb-3 text-sm font-semibold text-ink">Set up an alert</h3>

      <label className="mb-3 block text-xs text-muted">
        Alert type
        <select
          value={ruleType}
          onChange={(e) => {
            setRuleType(e.target.value as AlertRuleType);
            setSelected(null);
            setQuery("");
          }}
          className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
        >
          {Object.entries(RULE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>

      {ruleType === "restock" ? (
        <label className="block text-xs text-muted">
          Product name to watch for
          <input
            value={watchText}
            onChange={(e) => setWatchText(e.target.value)}
            placeholder="e.g. Scarlet & Violet Booster Bundle"
            required
            className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-3 py-2 text-sm text-ink outline-none placeholder:text-muted"
          />
        </label>
      ) : !selected ? (
        <div className="relative">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search cards or sealed products..."
            className="w-full rounded-lg border border-white/70 bg-white/60 px-3 py-2 text-sm text-ink outline-none placeholder:text-muted"
          />
          {results.length > 0 && (
            <div className="glass-frame absolute z-10 mt-1 max-h-64 w-full overflow-auto p-1">
              {results.map((item) => (
                <button
                  key={item.item_id}
                  type="button"
                  onClick={() => {
                    setSelected(item);
                    setResults([]);
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm hover:bg-white/50"
                >
                  <div className="kawaii-thumb flex h-7 w-7 shrink-0 items-center justify-center overflow-hidden bg-white/50 text-ink/50">
                    {item.image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={item.image_url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <PokeballPlaceholder className="h-4 w-4" />
                    )}
                  </div>
                  <span className="truncate">{item.name}</span>
                  <span className="ml-auto shrink-0 text-xs text-muted">
                    {item.item_type === "card" ? "card" : "pack"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg bg-white/50 px-3 py-2">
            <span className="text-sm text-ink">{selected.name}</span>
            <button type="button" onClick={() => setSelected(null)} className="text-xs text-muted underline">
              change
            </button>
          </div>

          <div className={`grid gap-2 ${ruleType === "pct_move" ? "grid-cols-2" : "grid-cols-1"}`}>
            <label className="text-xs text-muted">
              {ruleType === "pct_move" ? "% move" : "Price ($)"}
              <input
                type="number"
                min="0"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
              />
            </label>
            {ruleType === "pct_move" && (
              <label className="text-xs text-muted">
                Window (hours)
                <input
                  type="number"
                  min="1"
                  value={windowHours}
                  onChange={(e) => setWindowHours(e.target.value)}
                  required
                  className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
                />
              </label>
            )}
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={submitting || (needsItem && !selected)}
        className="glass-btn mt-3 w-full py-2 text-sm font-medium"
        data-active="true"
      >
        {submitting ? "Saving..." : "Create alert"}
      </button>

      {error && <p className="mt-2 text-xs text-loss">{error}</p>}
    </form>
  );
}
