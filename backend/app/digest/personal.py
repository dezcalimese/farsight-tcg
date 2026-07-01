from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Holding
from app.digest.generator import compute_price_moves


async def get_personal_highlight(session: AsyncSession, subscriber_id, period_days: int) -> str | None:
    """The single biggest mover among a subscriber's holdings this period, or
    None if they have no holdings or none moved. Folded into their digest."""
    result = await session.execute(select(Holding).where(Holding.subscriber_id == subscriber_id))
    holdings = result.scalars().all()
    if not holdings:
        return None

    holding_by_item_id = {str(h.card_id or h.sealed_product_id): h for h in holdings}

    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    moves = await compute_price_moves(session, since)
    relevant = [m for m in moves if m.item_id in holding_by_item_id]
    if not relevant:
        return None

    biggest = max(relevant, key=lambda m: abs(m.pct_change))
    holding = holding_by_item_id[biggest.item_id]
    dollar_change = round((biggest.price_now - biggest.price_then) * holding.quantity, 2)

    direction = "up" if biggest.pct_change >= 0 else "down"
    sign = "+" if dollar_change >= 0 else "-"
    return (
        f"Your {biggest.item_name} is {direction} {abs(biggest.pct_change):.1f}% this period "
        f"({sign}${abs(dollar_change):.2f})."
    )
