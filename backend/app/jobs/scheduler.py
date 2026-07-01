import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db.session import async_session_factory
from app.jobs.ingest import run_full_ingest

logger = logging.getLogger(__name__)


async def _poll_job() -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        counts = await run_full_ingest(session, settings)
        logger.info("poll complete: %s", counts)


def build_scheduler(poll_interval_minutes: int = 30) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_job,
        trigger=IntervalTrigger(minutes=poll_interval_minutes),
        id="poll_sources",
        next_run_time=None,  # first run scheduled by caller via run_now if desired
    )
    return scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    scheduler = build_scheduler()
    scheduler.start()
    await _poll_job()  # run once immediately on startup
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
