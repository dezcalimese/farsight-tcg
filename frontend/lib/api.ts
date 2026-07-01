export type PriceMove = {
  item_name: string;
  item_type: "card" | "sealed_product";
  price_then: number;
  price_now: number;
  pct_change: number;
};

export type RestockHighlight = {
  product_name: string;
  retailer: string | null;
  url: string | null;
  detected_at: string;
};

export type NewsHighlight = {
  title: string;
  url: string;
  source: string;
};

export type DigestData = {
  generated_at: string;
  period_days: number;
  trending_cards: PriceMove[];
  top_movers: PriceMove[];
  restocks: RestockHighlight[];
  news: NewsHighlight[];
};

export type Period = "daily" | "weekly";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getDigestData(period: Period): Promise<DigestData> {
  const res = await fetch(`${API_URL}/api/digest-data?period=${period}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load digest data: ${res.status}`);
  }
  return res.json();
}
