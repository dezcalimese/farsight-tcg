# Farsight

### PRD — Pokémon TCG Intelligence Feed

Reference: `01_PRODUCT_VISION.md`. If anything here conflicts with the vision doc, the vision doc wins.

---

## What we ARE building

- A backend that continuously ingests price data, restock signals, and news, and distills it into periodic digests
- A digest generator that produces a short, readable summary (trending cards, notable restocks, price movers, 1-2 news items) on a schedule
- Delivery to email and SMS (and Discord as a bonus channel) — this is the core deliverable
- A lightweight web dashboard to view the same info that goes in the digest, plus optional personal portfolio tracking and custom alert rules for people who want more than the default digest
- A signup flow: pick a channel, pick a cadence (daily/weekly), done — zero required configuration to get value

## What we are explicitly NOT building (v1)

Being precise about this list is the actual point of this document. Each of these is a reasonable feature for a mature product and a trap for v1.

- **No trading, checkout, or payments.** Nothing in this product moves money. If "buy this" is ever shown, it's a link out to TCGPlayer/retailer, never a transaction we process.
- **No user accounts with passwords at v1.** Email/phone + magic link or OTP. Do not build a password/auth system from scratch.
- **No mobile native app.** Web + PWA + SMS/email is the full surface. No App Store, no Play Store.
- **No scraping retailers directly (Target/Walmart/PokéCenter).** Bot detection requires paid proxies we don't want yet. Restock signal comes from Discord community channels or a manual/admin-fed source initially.
- **No multi-channel preference matrix.** One person picks one primary channel at signup. Don't build per-alert-type channel routing (e.g. "restocks via SMS, news via email") until the single-channel version is proven.
- **No social features.** No comments, no sharing portfolios, no following other users, no leaderboards.
- **No grading/authentication integration** (PSA submission tracking, etc.) — population data is read-only reference, not a workflow we manage.
- **No support for TCGs other than Pokémon.** Not Magic, not Yu-Gi-Oh, not Lorcana. Resist the urge to generalize the schema for "any TCG" — model it for Pokémon specifically and generalize later if it's ever needed.
- **No admin CMS / visual editor for the digest template.** The digest template lives in code. Editing it means editing code.
- **No real-time price ticking UI for v1.** The WebSocket live-update dashboard from the earlier portfolio-tracker scope is deferred — digests run on a schedule, not a live feed. If a dashboard exists, polling on page load is enough; don't build the pub/sub live layer until digests are working end to end.
- **No custom alert rule builder in v1.** That's a v2 feature once the default digest is proven useful. v1 alerting, if it exists at all, is a single toggle: "notify me of major moves," not a rules engine.
- **No settings/preferences page beyond channel + cadence.** See roadmap — settings is explicitly last.

## Core user flow (v1)

1. Person lands on the site, enters email or phone
2. Picks daily or weekly
3. Confirms via magic link/OTP
4. Starts receiving digests. That's it — no dashboard visit required to get value.

Optional, not required: they can visit a simple dashboard to see the same digest content as a webpage, and (later) add their own holdings.

## Success criteria for v1 ship

- A real person who has never touched the codebase can sign up and receive a genuinely useful digest within one cadence cycle, with zero support intervention.
