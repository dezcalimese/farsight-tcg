# Farsight

Pokémon TCG intelligence feed — see `docs/01_PRODUCT_VISION.md`, `docs/02_PRD.md`, and `docs/03_ROADMAP.md` for what this is and the build order. Build strictly follows the roadmap, phase by phase.

**Status: Phase 2 (delivery)** — data spine + digest generator + email/SMS/Discord delivery on a schedule. No UI yet.

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
uv run python -m scripts.send_digest_once                                 # generate + actually send
```

### Running the scheduler

```bash
cd backend
uv run python -m app.jobs.scheduler
```

Polls all three sources every 30 minutes, and generates + sends the digest on the configured cadence (`DIGEST_CADENCE`, default daily at `DIGEST_SEND_HOUR_UTC`). Any delivery channel without full credentials falls back to a stub that logs instead of sending.

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
    main.py        # FastAPI app (health check only until Phase 4+)
    config.py       # all env vars, pydantic-settings
    db/              # SQLAlchemy models + async session
    sources/          # PriceSource / NewsSource / RestockSource interfaces + impls
    digest/            # digest generator (Phase 1+)
    delivery/            # email/SMS/Discord notifiers (Phase 2+)
    jobs/                  # scheduled ingestion + digest jobs
    api/                     # FastAPI routers (Phase 4+)
  alembic/                    # migrations
frontend/                       # not scaffolded until Phase 4
```
