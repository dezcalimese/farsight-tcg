import logging

from app.config import Settings, get_settings
from app.db.session import async_session_factory
from app.delivery import get_notifiers
from app.digest.generator import generate_digest
from app.digest.render_html import render_html
from app.digest.render_text import render_text

logger = logging.getLogger(__name__)

_PERIOD_LABEL = {1: "Today", 7: "This Week"}


async def send_digest_job(settings: Settings | None = None) -> dict[str, bool]:
    settings = settings or get_settings()

    async with async_session_factory() as session:
        digest = await generate_digest(session, period_days=settings.digest_period_days)

    text_body = render_text(digest)
    html_body = render_html(digest)
    period_label = _PERIOD_LABEL.get(settings.digest_period_days, f"Last {settings.digest_period_days} Days")
    subject = f"Farsight — {period_label} in Pokemon TCG"

    results: dict[str, bool] = {}
    for notifier in get_notifiers(settings):
        ok = await notifier.send_digest(subject, text_body, html_body)
        results[notifier.name] = ok
        logger.info("digest send via %s: %s", notifier.name, "ok" if ok else "FAILED")

    return results
