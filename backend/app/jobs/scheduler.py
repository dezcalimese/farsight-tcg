import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db.session import async_session_factory
from app.jobs.alerts import evaluate_all_alerts
from app.jobs.ingest import run_full_ingest
from app.jobs.send_digest import send_digest_for_cadence

logger = logging.getLogger(__name__)


async def _poll_job() -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        counts = await run_full_ingest(session, settings)
        logger.info("poll complete: %s", counts)


async def _send_daily_job() -> None:
    # Discord is a community-wide broadcast, not per-subscriber; piggyback it on the daily run.
    results = await send_digest_for_cadence("daily", include_discord=True)
    logger.info("daily digest send complete: %s", results)


async def _send_weekly_job() -> None:
    results = await send_digest_for_cadence("weekly")
    logger.info("weekly digest send complete: %s", results)


async def _alert_check_job() -> None:
    results = await evaluate_all_alerts()
    logger.info("alert check complete: %s", results)


def build_scheduler(poll_interval_minutes: int = 30) -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_job,
        trigger=IntervalTrigger(minutes=poll_interval_minutes),
        id="poll_sources",
    )
    scheduler.add_job(
        _send_daily_job,
        trigger=CronTrigger(hour=settings.digest_send_hour_utc),
        id="send_daily_digest",
    )
    scheduler.add_job(
        _send_weekly_job,
        trigger=CronTrigger(day_of_week=settings.digest_send_weekday, hour=settings.digest_send_hour_utc),
        id="send_weekly_digest",
    )
    scheduler.add_job(
        _alert_check_job,
        trigger=IntervalTrigger(minutes=settings.alert_check_interval_minutes),
        id="check_alerts",
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
