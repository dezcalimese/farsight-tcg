# Farsight

### Roadmap — Pokémon TCG Intelligence Feed

Reference: `01_PRODUCT_VISION.md` and `02_PRD.md`. Build top to bottom. Do not skip ahead to a later phase because it's more interesting — the ordering is deliberate: prove the core loop works before anything else gets built on top of it.

---

## Phase 0 — Data spine
*Nothing user-facing yet. This phase just proves data flows in reliably.*

- Postgres schema: cards, sealed products, price snapshots, restock events, news items
- One price source wired end-to-end (TCGPlayer) writing real snapshots on a schedule
- One restock signal source wired (Discord channel watcher, or manual admin entry as a stopgap)
- Basic news ingestion (a small curated set of RSS feeds — PokeBeach, official Pokémon news — parsed and stored)
- **Exit criteria:** query the DB and see real, current data for cards/products/restocks/news. No UI required to verify this — a script that prints today's data is enough.

## Phase 1 — The digest (the actual product)
*This is the core feature. Everything before this exists to feed it; everything after exists to distribute or extend it.*

- Digest generator: given the last N days of data, produce a short structured summary — trending cards, notable restocks, top movers, 1-2 news items
- Render the digest as both plain text (for SMS) and HTML (for email)
- Manually trigger a digest generation and read the output yourself. Iterate on quality here before building any delivery — if the digest itself isn't good, delivery infrastructure doesn't matter.
- **Exit criteria:** you personally would forward this digest to a friend without editing it first.

## Phase 2 — Delivery
*Get the proven digest into people's hands.*

- Email delivery (Resend) — this is first because it's the simplest, cheapest, and easiest to debug
- SMS delivery (Twilio) — second, once email digest cadence is running clean
- Discord webhook delivery — bonus channel, reuses the same digest content
- Scheduled job: generate + send digest on cadence (daily/weekly)
- **Exit criteria:** a digest arrives in your own inbox/phone on schedule, unprompted, for a full week without manual intervention.

## Phase 3 — Signup flow
*Now that delivery works for you, let other people opt in.*

- Landing page: email/phone entry, cadence choice (daily/weekly)
- Magic link / OTP confirmation (no password auth)
- Unsubscribe flow (required before this ships to anyone but you)
- **Exit criteria:** a person outside your head can sign up and start receiving digests with zero help from you.

## Phase 4 — Read-only dashboard
*Give the digest content a home on the web for people who want to browse instead of wait for the next send.*

- Simple web view: today's trending cards, restock status, recent news — same data as the digest, browsable
- No live WebSocket updates yet — page-load polling is fine
- No portfolio tracking yet — this is the feed, viewable
- **Exit criteria:** the dashboard and the digest never disagree, because they're rendering from the same underlying data.

## Phase 5 — Personal portfolio layer
*Now layer in the "mine" feature for people who want more than the ambient feed.*

- Add holdings (card/product, qty, purchase price, date)
- Portfolio view: P&L per position, total value
- Fold a personal line into the digest ("your Mega Dragonite ex is up 12% this week") for people who've added holdings
- **Exit criteria:** adding a holding changes what shows up in your next digest, correctly.

## Phase 6 — Custom alerts
*Move past the default digest cadence for people who want tighter control.*

- Rule builder: price threshold, % move, restock watch
- Alert engine evaluates rules independent of the digest schedule and fires immediately when triggered
- Delivery reuses the same channels from Phase 2
- **Exit criteria:** a rule you set fires correctly and only when it should (no false positives, no missed triggers, over a real week of testing).

## Phase 7 — Settings
*Last, deliberately. Everything up to here should work well with sane defaults and no settings page at all.*

- Channel preferences (switch email ↔ SMS ↔ Discord, or use more than one)
- Cadence changes
- Per-category digest toggles (e.g. mute news, keep restocks)
- Account/data deletion
- **Exit criteria:** none — this phase is "as needed," not a hard gate. If Phases 1-6 are solid, settings is polish, not a blocker.

---

## The rule for the whole roadmap

If you're ever unsure what to build next, build whatever gets you closer to a real digest landing in a real inbox on schedule. That's the product. Everything else is in support of that one loop.
