"use client";

import type { AlertRule } from "@/lib/api";

function describe(rule: AlertRule): string {
  const name = rule.item_name ?? "your item";
  switch (rule.rule_type) {
    case "price_above":
      return `${name} rises above $${rule.threshold?.toFixed(2)}`;
    case "price_below":
      return `${name} drops below $${rule.threshold?.toFixed(2)}`;
    case "pct_move":
      return `${name} moves ±${rule.threshold?.toFixed(1)}% within ${rule.window_hours}h`;
    case "restock":
      return `Restock watch: "${rule.watch_text}"`;
  }
}

export function AlertRuleRow({ rule, onDelete }: { rule: AlertRule; onDelete: () => void }) {
  return (
    <div className="glass-panel-row flex items-center gap-3 px-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm text-ink">{describe(rule)}</div>
        {rule.last_triggered_at && (
          <div className="text-xs text-muted">
            Last fired {new Date(rule.last_triggered_at).toLocaleString()}
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={onDelete}
        aria-label="Remove alert"
        className="shrink-0 rounded-full px-2 py-1 text-xs text-muted hover:text-loss"
      >
        ✕
      </button>
    </div>
  );
}
