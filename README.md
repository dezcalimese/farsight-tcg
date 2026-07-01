# Farsight

Pokémon TCG intelligence feed — see `docs/01_PRODUCT_VISION.md`, `docs/02_PRD.md`, and `docs/03_ROADMAP.md` for what this is and the build order. Build strictly follows the roadmap, phase by phase.

**Status: Phase 4 (read-only dashboard)** — data spine, digest generator, email/SMS/Discord delivery, signup flow, and a browsable Next.js dashboard rendering the same data as the digest.

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

Polls all three sources every 30 minutes, sends the daily digest to active daily subscribers at `DIGEST_SEND_HOUR_UTC` (plus the Discord broadcast, if configured), and sends the weekly digest to active weekly subscribers on `DIGEST_SEND_WEEKDAY`. Any delivery channel without full credentials falls back to a stub that logs instead of sending.

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
    api/                     # signup/confirm/unsubscribe/dashboard routes + landing page template
  alembic/                    # migrations
frontend/                        # Next.js 14 App Router dashboard (Phase 4+)
  app/                            # dashboard page + layout
  lib/                             # API client / types shared with backend DigestData
```
