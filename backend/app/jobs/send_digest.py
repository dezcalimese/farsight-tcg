import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import Subscriber
from app.db.session import async_session_factory
from app.delivery import get_discord_notifier, get_email_notifier, get_sms_notifier
from app.digest.generator import generate_digest
from app.digest.personal import get_personal_highlight
from app.digest.render_html import render_html
from app.digest.render_text import render_text
from app.digest.schemas import DigestData

logger = logging.getLogger(__name__)

_PERIOD_LABEL = {1: "Today", 7: "This Week"}
_CADENCE_PERIOD_DAYS = {"daily": 1, "weekly": 7}


async def _active_subscribers(session: AsyncSession, cadence: str) -> list[Subscriber]:
    result = await session.execute(
        select(Subscriber).where(Subscriber.status == "active", Subscriber.cadence == cadence)
    )
    return list(result.scalars().all())


def _filtered_for_subscriber(digest: DigestData, subscriber: Subscriber) -> DigestData:
    """Applies the subscriber's per-category mutes (Settings > digest categories)."""
    return digest.model_copy(
        update={
            "trending_cards": [] if subscriber.mute_movers else digest.trending_cards,
            "top_movers": [] if subscriber.mute_movers else digest.top_movers,
            "restocks": [] if subscriber.mute_restocks else digest.restocks,
            "news": [] if subscriber.mute_news else digest.news,
        }
    )


async def send_digest_for_cadence(
    cadence: str, settings: Settings | None = None, include_discord: bool = False
) -> dict[str, int]:
    """Generates one digest for the given cadence and fans it out to every
    active subscriber on that cadence — on every channel they've enabled,
    filtered to the categories they haven't muted — plus optionally the
    Discord broadcast channel (which isn't per-subscriber)."""
    settings = settings or get_settings()
    period_days = _CADENCE_PERIOD_DAYS[cadence]
    period_label = _PERIOD_LABEL[period_days]
    subject = f"Farsight — {period_label} in Pokemon TCG"

    async with async_session_factory() as session:
        digest = await generate_digest(session, period_days=period_days)
        subscribers = await _active_subscribers(session, cadence)

        email_notifier = get_email_notifier(settings)
        sms_notifier = get_sms_notifier(settings)

        sent = 0
        failed = 0
        for subscriber in subscribers:
            subscriber_digest = _filtered_for_subscriber(digest, subscriber)
            unsubscribe_url = f"{settings.base_url}/api/unsubscribe?token={subscriber.unsubscribe_token}"
            portfolio_url = f"{settings.frontend_origin}/portfolio?token={subscriber.portfolio_token}"
            personal_line = await get_personal_highlight(session, subscriber.id, period_days)
            text_body = render_text(
                subscriber_digest, unsubscribe_url=unsubscribe_url, portfolio_url=portfolio_url,
                personal_line=personal_line,
            )
            html_body = render_html(
                subscriber_digest, unsubscribe_url=unsubscribe_url, portfolio_url=portfolio_url,
                personal_line=personal_line,
            )

            if subscriber.email_enabled:
                ok = await email_notifier.send_digest(subscriber.email, subject, text_body, html_body)
                sent += 1 if ok else 0
                failed += 0 if ok else 1
            if subscriber.sms_enabled:
                ok = await sms_notifier.send_digest(subscriber.phone, subject, text_body, html_body)
                sent += 1 if ok else 0
                failed += 0 if ok else 1

        if include_discord:
            discord_notifier = get_discord_notifier(settings)
            text_body = render_text(digest)
            html_body = render_html(digest)
            await discord_notifier.send_digest("", subject, text_body, html_body)

    logger.info("digest send (%s): %d subscribers, %d sent, %d failed", cadence, len(subscribers), sent, failed)
    return {"subscribers": len(subscribers), "sent": sent, "failed": failed}
