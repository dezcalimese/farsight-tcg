from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Subscriber


async def get_subscriber_by_portfolio_token(session: AsyncSession, token: str) -> Subscriber:
    result = await session.execute(select(Subscriber).where(Subscriber.portfolio_token == token))
    subscriber = result.scalar_one_or_none()
    if subscriber is None:
        raise HTTPException(404, "Invalid portfolio link.")
    return subscriber
