export type PriceMove = {
  item_id: string;
  item_name: string;
  item_type: "card" | "sealed_product";
  image_url: string | null;
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

export type PriceHistoryPoint = {
  time: number;
  value: number;
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

export async function getPriceHistory(
  itemType: "card" | "sealed_product",
  itemId: string,
  days: number
): Promise<PriceHistoryPoint[]> {
  const res = await fetch(
    `${API_URL}/api/price-history?item_type=${itemType}&item_id=${itemId}&days=${days}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Failed to load price history: ${res.status}`);
  }
  return res.json();
}

export type CatalogItem = {
  item_id: string;
  item_type: "card" | "sealed_product";
  name: string;
  image_url: string | null;
};

export type Holding = {
  id: string;
  item_type: "card" | "sealed_product";
  item_id: string;
  item_name: string;
  image_url: string | null;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
  current_price: number | null;
  cost_basis: number;
  market_value: number | null;
  pnl: number | null;
  pnl_pct: number | null;
};

export type Portfolio = {
  holdings: Holding[];
  total_cost: number;
  total_value: number | null;
  total_pnl: number | null;
};

export class PortfolioApiError extends Error {}

export async function searchCatalog(q: string): Promise<CatalogItem[]> {
  if (q.trim().length < 2) return [];
  const res = await fetch(`${API_URL}/api/catalog/search?q=${encodeURIComponent(q)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Catalog search failed: ${res.status}`);
  return res.json();
}

export async function getPortfolio(token: string): Promise<Portfolio> {
  const res = await fetch(`${API_URL}/api/portfolio?token=${encodeURIComponent(token)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new PortfolioApiError("Invalid or expired portfolio link.");
  return res.json();
}

export async function addHolding(
  token: string,
  body: {
    item_type: "card" | "sealed_product";
    item_id: string;
    quantity: number;
    purchase_price: number;
    purchase_date: string;
  }
): Promise<Holding> {
  const res = await fetch(`${API_URL}/api/portfolio/holdings?token=${encodeURIComponent(token)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new PortfolioApiError(data.detail ?? "Couldn't add that holding.");
  }
  return res.json();
}

export async function deleteHolding(token: string, holdingId: string): Promise<void> {
  const res = await fetch(
    `${API_URL}/api/portfolio/holdings/${holdingId}?token=${encodeURIComponent(token)}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new PortfolioApiError("Couldn't remove that holding.");
}

export type AlertRuleType = "price_above" | "price_below" | "pct_move" | "restock";

export type AlertRule = {
  id: string;
  rule_type: AlertRuleType;
  item_type: "card" | "sealed_product" | null;
  item_id: string | null;
  item_name: string | null;
  watch_text: string | null;
  threshold: number | null;
  window_hours: number;
  last_triggered_at: string | null;
};

export async function listAlerts(token: string): Promise<AlertRule[]> {
  const res = await fetch(`${API_URL}/api/alerts?token=${encodeURIComponent(token)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new PortfolioApiError("Couldn't load alerts.");
  return res.json();
}

export async function createAlert(
  token: string,
  body: {
    rule_type: AlertRuleType;
    item_type?: "card" | "sealed_product";
    item_id?: string;
    watch_text?: string;
    threshold?: number;
    window_hours?: number;
  }
): Promise<AlertRule> {
  const res = await fetch(`${API_URL}/api/alerts?token=${encodeURIComponent(token)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = data.detail;
    const message = Array.isArray(detail) ? detail[0]?.msg : detail;
    throw new PortfolioApiError(message ?? "Couldn't create that alert.");
  }
  return res.json();
}

export async function deleteAlert(token: string, ruleId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/alerts/${ruleId}?token=${encodeURIComponent(token)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new PortfolioApiError("Couldn't remove that alert.");
}
