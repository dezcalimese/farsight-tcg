import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import AlertRule, Card, RestockEvent, SealedProduct, Subscriber
from app.db.session import async_session_factory
from app.delivery.alert_notify import send_alert
from app.pricing import get_latest_price, get_pct_move

logger = logging.getLogger(__name__)


async def _item_name(session: AsyncSession, rule: AlertRule) -> str:
    if rule.card_id:
        card = await session.get(Card, rule.card_id)
        return card.name if card else "your card"
    if rule.sealed_product_id:
        product = await session.get(SealedProduct, rule.sealed_product_id)
        return product.name if product else "your product"
    return rule.watch_text or "your watch"


async def _evaluate_price_rule(session: AsyncSession, rule: AlertRule) -> str | None:
    item_type = "card" if rule.card_id else "sealed_product"
    item_id = rule.card_id or rule.sealed_product_id
    price = await get_latest_price(session, item_type, item_id)
    if price is None or rule.threshold is None:
        return None

    condition_met = price >= float(rule.threshold) if rule.rule_type == "price_above" else price <= float(rule.threshold)

    if condition_met and rule.is_armed:
        rule.is_armed = False
        rule.last_triggered_at = datetime.now(timezone.utc)
        name = await _item_name(session, rule)
        direction = "risen to" if rule.rule_type == "price_above" else "dropped to"
        return f"{name} has {direction} ${price:.2f} (your alert: {'>=' if rule.rule_type == 'price_above' else '<='} ${float(rule.threshold):.2f})."
    if not condition_met and not rule.is_armed:
        rule.is_armed = True  # condition cleared — rearm so a future crossing fires again
    return None


async def _evaluate_pct_move_rule(session: AsyncSession, rule: AlertRule) -> str | None:
    item_type = "card" if rule.card_id else "sealed_product"
    item_id = rule.card_id or rule.sealed_product_id
    since = datetime.now(timezone.utc) - timedelta(hours=rule.window_hours)
    pct_change = await get_pct_move(session, item_type, item_id, since)
    if pct_change is None or rule.threshold is None:
        return None

    condition_met = abs(pct_change) >= float(rule.threshold)

    if condition_met and rule.is_armed:
        rule.is_armed = False
        rule.last_triggered_at = datetime.now(timezone.utc)
        name = await _item_name(session, rule)
        direction = "up" if pct_change >= 0 else "down"
        return (
            f"{name} is {direction} {abs(pct_change):.1f}% over the last {rule.window_hours}h "
            f"(your alert: >= {float(rule.threshold):.1f}% move)."
        )
    if not condition_met and not rule.is_armed:
        rule.is_armed = True
    return None


async def _evaluate_restock_rule(session: AsyncSession, rule: AlertRule) -> str | None:
    since = rule.last_triggered_at or rule.created_at
    result = await session.execute(
        select(RestockEvent)
        .where(RestockEvent.detected_at > since)
        .where(RestockEvent.product_name_raw.ilike(f"%{rule.watch_text}%"))
        .order_by(RestockEvent.detected_at.desc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    if event is None:
        return None

    rule.last_triggered_at = event.detected_at
    retailer = f" at {event.retailer}" if event.retailer else ""
    return f"Restock watch \"{rule.watch_text}\": {event.product_name_raw}{retailer}."


async def evaluate_all_alerts(settings: Settings | None = None) -> dict[str, int]:
    """Runs independent of the digest schedule — checks every rule against
    current data and fires immediately on a new match. Edge-triggered dedupe
    (is_armed) means a level that stays past threshold only fires once."""
    settings = settings or get_settings()
    fired = 0
    checked = 0

    async with async_session_factory() as session:
        result = await session.execute(select(AlertRule))
        rules = result.scalars().all()

        for rule in rules:
            checked += 1
            if rule.rule_type in ("price_above", "price_below"):
                message = await _evaluate_price_rule(session, rule)
            elif rule.rule_type == "pct_move":
                message = await _evaluate_pct_move_rule(session, rule)
            else:
                message = await _evaluate_restock_rule(session, rule)

            if message:
                subscriber = await session.get(Subscriber, rule.subscriber_id)
                if subscriber and subscriber.status == "active":
                    ok = await send_alert(settings, subscriber, message)
                    if ok:
                        fired += 1
                        logger.info("alert fired for subscriber %s: %s", subscriber.id, message)

        await session.commit()

    return {"checked": checked, "fired": fired}
