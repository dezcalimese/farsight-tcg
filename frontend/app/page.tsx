import Link from "next/link";
import { getDigestData, type Period } from "@/lib/api";
import { EmptyState, MoveRow, NewsRow, RestockRow, SectionCard } from "./components";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: { period?: string };
}) {
  const period: Period = searchParams.period === "weekly" ? "weekly" : "daily";
  const digest = await getDigestData(period);

  const isEmpty =
    digest.trending_cards.length === 0 &&
    digest.top_movers.length === 0 &&
    digest.restocks.length === 0 &&
    digest.news.length === 0;

  const generatedAt = new Date(digest.generated_at).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <header className="mb-6">
        <h1 className="bg-brand-gradient bg-clip-text text-xl font-bold text-transparent">
          FARSIGHT
        </h1>
        <p className="mt-1 text-sm text-muted">Pokemon TCG market feed &middot; updated {generatedAt}</p>
      </header>

      <div className="mb-6 flex gap-2">
        <Link
          href="/?period=daily"
          className={`flex-1 rounded-lg border px-3 py-2 text-center text-sm ${
            period === "daily" ? "border-[#4f8ff0] text-white" : "border-transparent bg-white/5 text-muted"
          }`}
        >
          Today
        </Link>
        <Link
          href="/?period=weekly"
          className={`flex-1 rounded-lg border px-3 py-2 text-center text-sm ${
            period === "weekly" ? "border-[#4f8ff0] text-white" : "border-transparent bg-white/5 text-muted"
          }`}
        >
          This Week
        </Link>
      </div>

      {isEmpty && <EmptyState />}

      {digest.trending_cards.length > 0 && (
        <SectionCard title="Trending Cards">
          {digest.trending_cards.map((m) => (
            <MoveRow key={m.item_name} move={m} />
          ))}
        </SectionCard>
      )}

      {digest.top_movers.length > 0 && (
        <SectionCard title="Top Movers">
          {digest.top_movers.map((m) => (
            <MoveRow key={m.item_name} move={m} showType />
          ))}
        </SectionCard>
      )}

      {digest.restocks.length > 0 && (
        <SectionCard title="Restocks">
          {digest.restocks.map((r) => (
            <RestockRow key={r.product_name + r.detected_at} restock={r} />
          ))}
        </SectionCard>
      )}

      {digest.news.length > 0 && (
        <SectionCard title="News">
          {digest.news.map((n) => (
            <NewsRow key={n.url} news={n} />
          ))}
        </SectionCard>
      )}

      <footer className="mt-8 text-xs text-white/40">
        Want this in your inbox instead?{" "}
        <a href={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"} className="underline">
          Sign up
        </a>
        .
      </footer>
    </main>
  );
}
