import Link from "next/link";
import { getDigestData, type Period } from "@/lib/api";
import { EmptyState, NewsRow, RestockRow, SectionCard } from "./components";
import { MoveRow } from "./move-row";
import { MoversTabs } from "./movers-tabs";
import { AccountNav } from "./account-nav";
import { ThemeSwitcher } from "./theme-switcher";

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
    <main className="mx-auto max-w-xl px-3 py-6 sm:px-4 sm:py-8">
      <div className="glass-frame mb-6 p-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h1 className="font-heading accent-gradient-text text-2xl font-bold">
              Farsight <span className="kawaii-sparkle">✨</span>
            </h1>
            <p className="mt-1 text-sm text-muted">
              Pokemon TCG market feed &middot; updated {generatedAt}
            </p>
          </div>
          <ThemeSwitcher />
        </div>

        <AccountNav />

        <div className="flex gap-2">
          <Link
            href="/?period=daily"
            data-active={period === "daily"}
            className="glass-btn flex-1 py-2 text-center text-sm font-medium"
          >
            Today
          </Link>
          <Link
            href="/?period=weekly"
            data-active={period === "weekly"}
            className="glass-btn flex-1 py-2 text-center text-sm font-medium"
          >
            This Week
          </Link>
        </div>
      </div>

      {isEmpty && <EmptyState />}

      {digest.trending_cards.length > 0 && (
        <SectionCard title="Trending Cards">
          {digest.trending_cards.map((m) => (
            <MoveRow key={m.item_id} move={m} period={period} />
          ))}
        </SectionCard>
      )}

      {digest.top_movers.length > 0 && (
        <section className="mb-6">
          <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">Top Movers</h2>
          <MoversTabs moves={digest.top_movers} period={period} />
        </section>
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

      <footer className="mt-8 text-xs text-muted">
        Want this in your inbox instead? (づ｡◕‿‿◕｡)づ{" "}
        <a href={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"} className="underline">
          Sign up
        </a>
        .
      </footer>
    </main>
  );
}
