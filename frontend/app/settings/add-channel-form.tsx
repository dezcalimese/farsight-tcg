"use client";

import { useState } from "react";
import { addChannel, confirmSmsChannel, type SettingsData } from "@/lib/api";

export function AddChannelForm({
  token,
  channel,
  onUpdated,
}: {
  token: string;
  channel: "email" | "sms";
  onUpdated: (settings: SettingsData) => void;
}) {
  const [contact, setContact] = useState("");
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const settings = await addChannel(token, { channel, contact });
      onUpdated(settings);
      setPending(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirm(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const settings = await confirmSmsChannel(token, code);
      onUpdated(settings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  if (pending && channel === "email") {
    return <p className="text-xs text-muted">Check your email for a confirmation link.</p>;
  }

  if (pending && channel === "sms") {
    return (
      <form onSubmit={handleConfirm} className="flex gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="123456"
          inputMode="numeric"
          required
          className="min-w-0 flex-1 rounded-lg border border-white/70 bg-white/60 px-3 py-2 text-sm text-ink outline-none placeholder:text-muted"
        />
        <button type="submit" disabled={submitting} className="glass-btn px-4 text-sm font-medium" data-active="true">
          Confirm
        </button>
        {error && <p className="text-xs text-loss">{error}</p>}
      </form>
    );
  }

  return (
    <form onSubmit={handleAdd} className="flex gap-2">
      <input
        value={contact}
        onChange={(e) => setContact(e.target.value)}
        placeholder={channel === "email" ? "you@example.com" : "+15551234567"}
        type={channel === "email" ? "email" : "tel"}
        required
        className="min-w-0 flex-1 rounded-lg border border-white/70 bg-white/60 px-3 py-2 text-sm text-ink outline-none placeholder:text-muted"
      />
      <button type="submit" disabled={submitting} className="glass-btn px-4 text-sm font-medium" data-active="true">
        Add
      </button>
      {error && <p className="text-xs text-loss">{error}</p>}
    </form>
  );
}
