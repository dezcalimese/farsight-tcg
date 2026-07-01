"""One-shot ingest run, useful for local dev and the Phase 0 exit-criteria check."""

import asyncio
import logging

from app.config import get_settings
from app.db.session import async_session_factory
from app.jobs.ingest import run_full_ingest


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    async with async_session_factory() as session:
        counts = await run_full_ingest(session, settings)
        print(f"ingest complete: {counts}")


if __name__ == "__main__":
    asyncio.run(main())
