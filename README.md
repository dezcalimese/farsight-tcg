# Farsight

Pokémon TCG intelligence feed — see `docs/01_PRODUCT_VISION.md`, `docs/02_PRD.md`, and `docs/03_ROADMAP.md` for what this is and the build order. Build strictly follows the roadmap, phase by phase.

**Status: Phase 3 (signup flow)** — data spine, digest generator, email/SMS/Discord delivery, and a real signup flow (landing page + magic link/OTP + unsubscribe). Full frontend still comes in Phase 4.

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

## Repo structure

```
backend/
  app/
    main.py        # FastAPI app: landing page + signup API + health check
    config.py       # all env vars, pydantic-settings
    db/              # SQLAlchemy models + async session
    sources/          # PriceSource / NewsSource / RestockSource interfaces + impls
    digest/            # digest generator + text/HTML renderers
    delivery/            # email/SMS/Discord notifiers + magic-link/OTP senders
    jobs/                  # scheduled ingestion + digest send jobs
    api/                     # signup/confirm/unsubscribe routes + landing page template
  alembic/                    # migrations
frontend/                       # not scaffolded until Phase 4
```
