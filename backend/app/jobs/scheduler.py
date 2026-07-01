import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db.session import async_session_factory
from app.jobs.ingest import run_full_ingest
from app.jobs.send_digest import send_digest_job

logger = logging.getLogger(__name__)


async def _poll_job() -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        counts = await run_full_ingest(session, settings)
        logger.info("poll complete: %s", counts)


async def _send_job() -> None:
    results = await send_digest_job()
    logger.info("digest send complete: %s", results)


def _digest_trigger(settings) -> CronTrigger:
    if settings.digest_cadence == "weekly":
        return CronTrigger(day_of_week=settings.digest_send_weekday, hour=settings.digest_send_hour_utc)
    return CronTrigger(hour=settings.digest_send_hour_utc)


def build_scheduler(poll_interval_minutes: int = 30) -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_job,
        trigger=IntervalTrigger(minutes=poll_interval_minutes),
        id="poll_sources",
    )
    scheduler.add_job(
        _send_job,
        trigger=_digest_trigger(settings),
        id="send_digest",
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
