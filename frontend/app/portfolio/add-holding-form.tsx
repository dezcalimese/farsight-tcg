"use client";

import { useEffect, useState } from "react";
import { addHolding, searchCatalog, type CatalogItem, type Holding } from "@/lib/api";
import { PokeballPlaceholder } from "../motif-icon";

export function AddHoldingForm({
  token,
  onAdded,
}: {
  token: string;
  onAdded: (holding: Holding) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CatalogItem[]>([]);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [quantity, setQuantity] = useState("1");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const holding = await addHolding(token, {
        item_type: selected.item_type,
        item_id: selected.item_id,
        quantity: Number(quantity),
        purchase_price: Number(purchasePrice),
        purchase_date: new Date(purchaseDate).toISOString(),
      });
      onAdded(holding);
      setSelected(null);
      setQuery("");
      setQuantity("1");
      setPurchasePrice("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass-panel p-4">
      <h3 className="mb-3 text-sm font-semibold text-ink">Add a holding</h3>

      {!selected ? (
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
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center kawaii-thumb overflow-hidden bg-white/50 text-ink/50">
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
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="text-xs text-muted underline"
            >
              change
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <label className="text-xs text-muted">
              Qty
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
              />
            </label>
            <label className="text-xs text-muted">
              Price paid
              <input
                type="number"
                min="0"
                step="0.01"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
              />
            </label>
            <label className="text-xs text-muted">
              Date
              <input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-white/70 bg-white/60 px-2 py-1.5 text-sm text-ink outline-none"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="glass-btn w-full py-2 text-sm font-medium"
            data-active="true"
          >
            {submitting ? "Adding..." : "Add to portfolio"}
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-loss">{error}</p>}
    </form>
  );
}
