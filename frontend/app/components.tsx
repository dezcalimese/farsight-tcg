import type { NewsHighlight, RestockHighlight } from "@/lib/api";

export function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">{title}</h2>
      <div className="glass-panel overflow-hidden">{children}</div>
    </section>
  );
}

export function RestockRow({ restock }: { restock: RestockHighlight }) {
  return (
    <div className="glass-panel-row px-4 py-3 text-sm text-ink">
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
      className="glass-panel-row block px-4 py-3 transition-colors hover:bg-white/40"
    >
      <div className="text-sm text-accent-1">{news.title}</div>
      <div className="mt-0.5 text-xs text-muted">{news.source}</div>
    </a>
  );
}

export function EmptyState() {
  return (
    <div className="glass-panel px-5 py-6 text-sm text-ink/70">
      (｡•́︿•̀｡) Nothing to report right now — check back next cycle!
    </div>
  );
}
