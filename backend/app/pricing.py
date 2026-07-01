import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceSnapshot


async def get_latest_price(session: AsyncSession, item_type: str, item_id: uuid.UUID) -> float | None:
    column = PriceSnapshot.card_id if item_type == "card" else PriceSnapshot.sealed_product_id
    result = await session.execute(
        select(PriceSnapshot.market_price)
        .where(column == item_id)
        .where(PriceSnapshot.market_price.is_not(None))
        .order_by(PriceSnapshot.captured_at.desc())
        .limit(1)
    )
    price = result.scalar_one_or_none()
    return float(price) if price is not None else None


async def get_pct_move(
    session: AsyncSession, item_type: str, item_id: uuid.UUID, since: datetime
) -> float | None:
    """% change between the first and last snapshot for this item since `since`."""
    column = PriceSnapshot.card_id if item_type == "card" else PriceSnapshot.sealed_product_id
    result = await session.execute(
        select(PriceSnapshot.market_price)
        .where(column == item_id)
        .where(PriceSnapshot.captured_at >= since)
        .where(PriceSnapshot.market_price.is_not(None))
        .order_by(PriceSnapshot.captured_at.asc())
    )
    prices = [float(p) for p in result.scalars().all()]
    if len(prices) < 2 or prices[0] == 0:
        return None
    return (prices[-1] - prices[0]) / prices[0] * 100
