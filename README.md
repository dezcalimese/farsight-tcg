# Farsight

A Pokémon TCG intelligence feed. Farsight ingests card/sealed-product prices (TCGPlayer), restock signals (Discord), and news (RSS), then turns them into a periodic digest — trending cards, top movers, restocks, and news — delivered by email, SMS, or Discord on a cadence you pick at signup. No account or dashboard required to get value from it.

On top of the digest sits an optional, deeper layer: a browsable web dashboard, a personal portfolio (holdings, live P&L, a personalized line folded into your digest), and custom alerts (price thresholds, % moves, restock watches) that fire independently of the digest schedule the moment a rule matches. Everything is gated by simple magic-link/OTP tokens — no passwords.

See `docs/01_PRODUCT_VISION.md`, `docs/02_PRD.md`, and `docs/03_ROADMAP.md` for the product thinking and phased build order this repo follows.

**Status:** Phases 0–6 complete — data spine, digest generation, email/SMS/Discord delivery, signup flow, dashboard, portfolio, and custom alerts. Phase 7 (settings) is the only thing left on the roadmap.

## Local dev

```bash
cp .env.example .env   # fill in what you have; every key is optional locally

docker compose up -d   # postgres + redis

cd backend
uv sync                # or: pip install -e .
uv run alembic upgrade head

# run the poller once and print what landed in the DB
uv run python -m app.jobs.ingest_once   # one-shot ingest
uv run python -m scripts.print_today    # Phase 0 exit criteria: today's data
```

No API key blocks local dev — any source without credentials configured (TCGPlayer, Discord) falls back to a stub source that writes clearly-marked fake data so the whole pipeline still runs end-to-end. RSS news requires no key and always runs for real.

### Digest

```bash
cd backend
uv run python -m scripts.generate_digest 7 --html-out /tmp/digest.html   # generate + review, don't send
uv run python -m scripts.send_digest_once daily                           # generate + actually send to active daily subscribers
```

### Signup flow

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/` for the landing page. Email signups get a magic link (via Resend, or logged to the console if `RESEND_API_KEY` isn't set); SMS signups get a 6-digit code (via Twilio, or logged to the console). Every digest includes a personalized unsubscribe link.

### Running the scheduler

```bash
cd backend
uv run python -m app.jobs.scheduler
```

Polls all three sources every 30 minutes, sends the daily digest to active daily subscribers at `DIGEST_SEND_HOUR_UTC` (plus the Discord broadcast, if configured), sends the weekly digest to active weekly subscribers on `DIGEST_SEND_WEEKDAY`, and checks alert rules every `ALERT_CHECK_INTERVAL_MINUTES` (default 5) independent of the digest schedule. Any delivery channel without full credentials falls back to a stub that logs instead of sending.

### Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Dashboard (frontend)

```bash
cd frontend
cp .env.local.example .env.local   # points at the backend, defaults to localhost:8000
bun install
bun run dev
```

Visit `http://localhost:3000`. It's a read-only view of the same `/api/digest-data` endpoint the email/SMS digest is generated from — page-load only, no live updates, so it can never disagree with what gets sent out. The backend must be running (`uv run uvicorn app.main:app --reload` from `backend/`) with `FRONTEND_ORIGIN` set to match (default `http://localhost:3000`, already covers this).

Modern glassmorphic UI with 4 selectable pastel themes (Xatu default, Pikachu, Clefairy, Azumarill), persisted to `localStorage`. Top Movers splits into Cards/Packs tabs. Clicking any card/pack row expands a [liveline](https://www.npmjs.com/package/liveline)-powered price history chart, backed by `GET /api/price-history`. Card/product thumbnails come from TCGPlayer's catalog `imageUrl` when a real `TCGPLAYER_CLIENT_ID`/`SECRET` is configured; otherwise rows show a placeholder icon (stub price source doesn't set images).

### Portfolio

Every subscriber gets a permanent, unguessable `portfolio_token` at signup (separate from their unsubscribe token, so leaking one link can't do the other's job) — no passwords, consistent with the rest of the app's magic-link approach. The link is shown on the signup confirmation page and in the footer of every digest ("Your portfolio: ...").

Visit `http://localhost:3000/portfolio?token=<portfolio_token>` to add holdings (search the existing card/sealed-product catalog, set quantity/price paid/date), see live P&L against the latest ingested price, and remove holdings. `GET /api/portfolio`, `POST /api/portfolio/holdings`, and `DELETE /api/portfolio/holdings/{id}` are all gated on that token.

Subscribers with at least one holding get a personalized line folded into their digest — the single biggest mover among their holdings this period (e.g. "Your Charizard ex is up 12.3% this period (+$45.20)."). Computed per-subscriber in `app/digest/personal.py`, reusing the same price-move calculation the digest and dashboard already share.

### Custom alerts

Set up on the portfolio page (same `portfolio_token`, no separate login). Three rule types, matching the roadmap exactly:

- **Price threshold** (`price_above` / `price_below`) — fires when an item's latest price crosses your threshold
- **% move** (`pct_move`) — fires when an item moves by more than N% within a rolling window (hours, configurable)
- **Restock watch** (`restock`) — fires when a new restock event's product name matches your watch text

`app/jobs/alerts.py` evaluates every rule on its own schedule (`ALERT_CHECK_INTERVAL_MINUTES`), completely independent of the digest cron jobs, and fires immediately through the same email/SMS notifiers the digest uses. Price/% rules are edge-triggered via an `is_armed` flag on `AlertRule` — once fired, a rule won't refire while the condition stays true; it rearms the moment the condition clears, so a real second crossing fires again. Restock rules dedupe via a `last_triggered_at` watermark instead, since restocks are discrete events rather than a continuous level.

## Repo structure

```
backend/
  app/
    main.py        # FastAPI app: landing page + signup API + dashboard API + health check
    config.py       # all env vars, pydantic-settings
    db/              # SQLAlchemy models + async session
    sources/          # PriceSource / NewsSource / RestockSource interfaces + impls
    digest/            # digest generator + text/HTML renderers
    delivery/            # email/SMS/Discord notifiers + magic-link/OTP senders
    jobs/                  # scheduled ingestion + digest send jobs
    api/                     # signup/confirm/unsubscribe/dashboard/portfolio routes + landing page template
  alembic/                    # migrations
frontend/                        # Next.js 14 App Router (Phase 4+)
  app/                            # dashboard page + layout + theme system
  app/portfolio/                   # token-gated portfolio page (Phase 5)
  lib/                               # API client / types shared with backend DigestData
```
