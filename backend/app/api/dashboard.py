import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceSnapshot
from app.db.session import get_session
from app.digest.generator import generate_digest
from app.digest.schemas import DigestData

router = APIRouter(prefix="/api")

_PERIOD_DAYS = {"daily": 1, "weekly": 7}


@router.get("/digest-data", response_model=DigestData)
async def digest_data(
    period: Literal["daily", "weekly"] = "daily",
    session: AsyncSession = Depends(get_session),
) -> DigestData:
    """Same aggregation the email/SMS digest uses — the dashboard renders this
    directly so it can never disagree with what gets sent out."""
    return await generate_digest(session, period_days=_PERIOD_DAYS[period])


class PriceHistoryPoint(BaseModel):
    time: int  # unix epoch seconds, for liveline
    value: float


@router.get("/price-history", response_model=list[PriceHistoryPoint])
async def price_history(
    item_type: Literal["card", "sealed_product"],
    item_id: uuid.UUID,
    days: int = 7,
    session: AsyncSession = Depends(get_session),
) -> list[PriceHistoryPoint]:
    if days < 1 or days > 90:
        raise HTTPException(422, "days must be between 1 and 90")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    column = PriceSnapshot.card_id if item_type == "card" else PriceSnapshot.sealed_product_id

    result = await session.execute(
        select(PriceSnapshot)
        .where(column == item_id)
        .where(PriceSnapshot.captured_at >= since)
        .where(PriceSnapshot.market_price.is_not(None))
        .order_by(PriceSnapshot.captured_at.asc())
    )
    return [
        PriceHistoryPoint(time=int(snap.captured_at.timestamp()), value=float(snap.market_price))
        for snap in result.scalars().all()
    ]
