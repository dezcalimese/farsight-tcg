"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  deleteAccount,
  getSettings,
  toggleChannels,
  updateSettings,
  type Period,
  type SettingsData,
  PortfolioApiError,
} from "@/lib/api";
import { ThemeSwitcher } from "../theme-switcher";
import { AddChannelForm } from "./add-channel-form";

function ToggleRow({
  label,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-center justify-between gap-3 px-4 py-3">
      <span className="text-sm text-ink">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="h-5 w-5 accent-[var(--accent-1)]"
      />
    </label>
  );
}

export default function SettingsPage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  const token = searchParams.token ?? "";
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteConfirming, setDeleteConfirming] = useState(false);
  const [deleted, setDeleted] = useState(false);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    getSettings(token)
      .then(setSettings)
      .catch((err) => setError(err instanceof PortfolioApiError ? err.message : "Something went wrong."))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleCadence(cadence: Period) {
    const updated = await updateSettings(token, { cadence });
    setSettings(updated);
  }

  async function handleMute(field: "mute_movers" | "mute_restocks" | "mute_news", value: boolean) {
    const updated = await updateSettings(token, { [field]: value });
    setSettings(updated);
  }

  async function handleChannelToggle(field: "email_enabled" | "sms_enabled", value: boolean) {
    setError(null);
    try {
      const updated = await toggleChannels(token, { [field]: value });
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  async function handleDelete() {
    if (!deleteConfirming) {
      setDeleteConfirming(true);
      return;
    }
    await deleteAccount(token);
    setDeleted(true);
  }

  if (deleted) {
    return (
      <main className="mx-auto max-w-xl px-3 py-6 sm:px-4 sm:py-8">
        <div className="glass-frame p-5 text-sm text-ink/80">
          Your account and all its data (holdings, alerts, preferences) have been deleted. You won&apos;t
          receive any more Farsight digests.
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-3 py-6 sm:px-4 sm:py-8">
      <div className="glass-frame mb-6 p-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h1 className="font-heading accent-gradient-text text-2xl font-bold">
              Settings <span className="kawaii-sparkle">⚙️</span>
            </h1>
            <p className="mt-1 text-sm text-muted">Delivery, cadence, and what shows up in your digest.</p>
          </div>
          <ThemeSwitcher />
        </div>

        <div className="flex gap-2">
          <Link href="/" className="glass-btn px-3 py-1.5 text-xs font-medium">
            ← Dashboard
          </Link>
          <Link href={`/portfolio?token=${token}`} className="glass-btn px-3 py-1.5 text-xs font-medium">
            Portfolio
          </Link>
        </div>
      </div>

      {!token && (
        <div className="glass-panel px-5 py-6 text-sm text-ink/80">
          No settings link found. Use the link from your Farsight signup confirmation, portfolio page, or
          digest email/text to get here.
        </div>
      )}

      {token && loading && <div className="glass-panel px-5 py-6 text-sm text-muted">Loading...</div>}

      {token && !loading && error && !settings && (
        <div className="glass-panel px-5 py-6 text-sm text-loss">{error}</div>
      )}

      {settings && (
        <>
          <section className="mb-6">
            <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">Cadence</h2>
            <div className="glass-panel flex gap-2 p-2">
              <button
                type="button"
                data-active={settings.cadence === "daily"}
                onClick={() => handleCadence("daily")}
                className="glass-btn flex-1 py-2 text-sm font-medium"
              >
                Daily
              </button>
              <button
                type="button"
                data-active={settings.cadence === "weekly"}
                onClick={() => handleCadence("weekly")}
                className="glass-btn flex-1 py-2 text-sm font-medium"
              >
                Weekly
              </button>
            </div>
          </section>

          <section className="mb-6">
            <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">
              Digest categories
            </h2>
            <div className="glass-panel divide-y divide-white/50 overflow-hidden">
              <ToggleRow
                label="Trending cards & top movers"
                checked={!settings.mute_movers}
                onChange={(v) => handleMute("mute_movers", !v)}
              />
              <ToggleRow
                label="Restocks"
                checked={!settings.mute_restocks}
                onChange={(v) => handleMute("mute_restocks", !v)}
              />
              <ToggleRow
                label="News"
                checked={!settings.mute_news}
                onChange={(v) => handleMute("mute_news", !v)}
              />
            </div>
          </section>

          <section className="mb-6">
            <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-ink/80">
              Delivery channels
            </h2>
            <div className="glass-panel divide-y divide-white/50 overflow-hidden p-4">
              <div className="pb-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-ink">Email</span>
                  {settings.email && (
                    <label className="flex items-center gap-2 text-xs text-muted">
                      Enabled
                      <input
                        type="checkbox"
                        checked={settings.email_enabled}
                        onChange={(e) => handleChannelToggle("email_enabled", e.target.checked)}
                        className="h-4 w-4 accent-[var(--accent-1)]"
                      />
                    </label>
                  )}
                </div>
                {settings.email ? (
                  <p className="text-xs text-muted">{settings.email}</p>
                ) : (
                  <AddChannelForm token={token} channel="email" onUpdated={setSettings} />
                )}
              </div>
              <div className="pt-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-ink">Text (SMS)</span>
                  {settings.phone && (
                    <label className="flex items-center gap-2 text-xs text-muted">
                      Enabled
                      <input
                        type="checkbox"
                        checked={settings.sms_enabled}
                        onChange={(e) => handleChannelToggle("sms_enabled", e.target.checked)}
                        className="h-4 w-4 accent-[var(--accent-1)]"
                      />
                    </label>
                  )}
                </div>
                {settings.phone ? (
                  <p className="text-xs text-muted">{settings.phone}</p>
                ) : (
                  <AddChannelForm token={token} channel="sms" onUpdated={setSettings} />
                )}
              </div>
              {error && <p className="mt-3 text-xs text-loss">{error}</p>}
            </div>
          </section>

          <section>
            <h2 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-loss/80">Danger zone</h2>
            <div className="glass-panel p-4">
              <p className="mb-3 text-xs text-muted">
                Deletes your account and everything tied to it — holdings, alerts, preferences. You'll stop
                receiving digests immediately. This can't be undone.
              </p>
              <button
                type="button"
                onClick={handleDelete}
                className="glass-btn w-full py-2 text-sm font-medium text-loss"
              >
                {deleteConfirming ? "Click again to confirm deletion" : "Delete my account"}
              </button>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
