from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
