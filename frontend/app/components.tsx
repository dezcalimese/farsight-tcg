import type { NewsHighlight, PriceMove, RestockHighlight } from "@/lib/api";

export function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-white/90">{title}</h2>
      <div className="overflow-hidden rounded-xl border border-border bg-surface/80 backdrop-blur">
        {children}
      </div>
    </section>
  );
}

export function MoveRow({ move, showType = false }: { move: PriceMove; showType?: boolean }) {
  const positive = move.pct_change >= 0;
  return (
    <div className="border-b border-border px-4 py-3 last:border-b-0">
      <div className="text-sm text-white/90">
        {move.item_name}
        {showType && (
          <span className="ml-1.5 text-xs text-muted">({move.item_type.replace("_", " ")})</span>
        )}
      </div>
      <div className={`mt-0.5 font-mono text-[13px] ${positive ? "text-gain" : "text-loss"}`}>
        {positive ? "+" : ""}
        {move.pct_change.toFixed(1)}% &middot; ${move.price_then.toFixed(2)} &rarr; $
        {move.price_now.toFixed(2)}
      </div>
    </div>
  );
}

export function RestockRow({ restock }: { restock: RestockHighlight }) {
  return (
    <div className="border-b border-border px-4 py-3 text-sm text-white/90 last:border-b-0">
      {restock.product_name}
      {restock.retailer && <span className="ml-1.5 text-xs text-muted">({restock.retailer})</span>}
    </div>
  );
}

export function NewsRow({ news }: { news: NewsHighlight }) {
  return (
    <a
      href={news.url}
      target="_blank"
      rel="noreferrer"
      className="block border-b border-border px-4 py-3 last:border-b-0 hover:bg-white/[0.03]"
    >
      <div className="text-sm text-[#4f8ff0]">{news.title}</div>
      <div className="mt-0.5 text-xs text-muted">{news.source}</div>
    </a>
  );
}

export function EmptyState() {
  return (
    <div className="rounded-xl border border-border bg-surface/80 px-5 py-6 text-sm text-white/70">
      No notable market activity to report right now. Check back next cycle.
    </div>
  );
}
