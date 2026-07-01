"use client";

import { useEffect, useState } from "react";
import {
  deleteHolding,
  getPortfolio,
  type Holding,
  type Portfolio,
  PortfolioApiError,
} from "@/lib/api";
import { ThemeSwitcher } from "../theme-switcher";
import { AddHoldingForm } from "./add-holding-form";
import { HoldingRow } from "./holding-row";

export default function PortfolioPage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  const token = searchParams.token ?? "";
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    getPortfolio(token)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof PortfolioApiError ? err.message : "Something went wrong."))
      .finally(() => setLoading(false));
  }, [token]);

  function handleAdded(holding: Holding) {
    setPortfolio((prev) =>
      prev
        ? {
            ...prev,
            holdings: [holding, ...prev.holdings],
            total_cost: prev.total_cost + holding.cost_basis,
            total_value:
              prev.total_value !== null && holding.market_value !== null
                ? prev.total_value + holding.market_value
                : null,
            total_pnl:
              prev.total_pnl !== null && holding.pnl !== null ? prev.total_pnl + holding.pnl : null,
          }
        : prev
    );
  }

  async function handleDelete(holding: Holding) {
    await deleteHolding(token, holding.id);
    setPortfolio((prev) =>
      prev
        ? {
            ...prev,
            holdings: prev.holdings.filter((h) => h.id !== holding.id),
            total_cost: prev.total_cost - holding.cost_basis,
            total_value:
              prev.total_value !== null && holding.market_value !== null
                ? prev.total_value - holding.market_value
                : prev.total_value,
            total_pnl:
              prev.total_pnl !== null && holding.pnl !== null ? prev.total_pnl - holding.pnl : prev.total_pnl,
          }
        : prev
    );
  }

  return (
    <main className="mx-auto max-w-xl px-3 py-6 sm:px-4 sm:py-8">
      <div className="glass-frame mb-6 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="font-heading accent-gradient-text text-2xl font-bold">
              My Portfolio <span className="kawaii-sparkle">💖</span>
            </h1>
            <p className="mt-1 text-sm text-muted">Your Pokemon TCG holdings, tracked against live prices.</p>
          </div>
          <ThemeSwitcher />
        </div>
      </div>

      {!token && (
        <div className="glass-panel px-5 py-6 text-sm text-ink/80">
          (๑•́ ₃ •̀๑) No portfolio link found. Use the &ldquo;Set up your portfolio&rdquo; link from your
          Farsight signup confirmation or digest email/text to get here.
        </div>
      )}

      {token && loading && (
        <div className="glass-panel px-5 py-6 text-sm text-muted">Loading your portfolio... (◕‿◕)</div>
      )}

      {token && !loading && error && (
        <div className="glass-panel px-5 py-6 text-sm text-loss">{error}</div>
      )}

      {portfolio && (
        <>
          <div className="glass-panel mb-6 grid grid-cols-3 divide-x divide-white/50 overflow-hidden">
            <div className="px-4 py-3 text-center">
              <div className="text-xs text-muted">Cost basis</div>
              <div className="mt-1 font-mono text-sm text-ink">${portfolio.total_cost.toFixed(2)}</div>
            </div>
            <div className="px-4 py-3 text-center">
              <div className="text-xs text-muted">Value</div>
              <div className="mt-1 font-mono text-sm text-ink">
                {portfolio.total_value !== null ? `$${portfolio.total_value.toFixed(2)}` : "—"}
              </div>
            </div>
            <div className="px-4 py-3 text-center">
              <div className="text-xs text-muted">P&amp;L</div>
              <div
                className={`mt-1 font-mono text-sm ${
                  portfolio.total_pnl !== null && portfolio.total_pnl >= 0 ? "text-gain" : "text-loss"
                }`}
              >
                {portfolio.total_pnl !== null
                  ? `${portfolio.total_pnl >= 0 ? "+" : ""}$${portfolio.total_pnl.toFixed(2)}`
                  : "—"}
              </div>
            </div>
          </div>

          {portfolio.holdings.length > 0 ? (
            <section className="mb-6">
              <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">Holdings</h2>
              <div className="glass-panel overflow-hidden">
                {portfolio.holdings.map((h) => (
                  <HoldingRow key={h.id} holding={h} onDelete={() => handleDelete(h)} />
                ))}
              </div>
            </section>
          ) : (
            <div className="glass-panel mb-6 px-5 py-6 text-center text-sm text-ink/70">
              (｡･ω･｡) No holdings yet — add your first card or pack below!
            </div>
          )}

          <AddHoldingForm token={token} onAdded={handleAdded} />
        </>
      )}
    </main>
  );
}
