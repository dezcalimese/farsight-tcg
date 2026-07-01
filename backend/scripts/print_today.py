"""Phase 0 exit criteria: query the DB and print today's real data.

Usage: python -m scripts.print_today  (run from backend/)
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models import NewsItem, PriceSnapshot, RestockEvent
from app.db.session import async_session_factory


async def main() -> None:
    since = datetime.now(timezone.utc) - timedelta(days=1)

    async with async_session_factory() as session:
        prices = (
            await session.execute(
                select(PriceSnapshot)
                .where(PriceSnapshot.captured_at >= since)
                .order_by(PriceSnapshot.captured_at.desc())
                .limit(20)
            )
        ).scalars().all()

        restocks = (
            await session.execute(
                select(RestockEvent)
                .where(RestockEvent.detected_at >= since)
                .order_by(RestockEvent.detected_at.desc())
                .limit(20)
            )
        ).scalars().all()

        news = (
            await session.execute(
                select(NewsItem).order_by(NewsItem.fetched_at.desc()).limit(10)
            )
        ).scalars().all()

    print(f"=== Price snapshots (last 24h): {len(prices)} ===")
    for p in prices:
        item = p.card_id or p.sealed_product_id
        print(f"  [{p.source}] item={item} market=${p.market_price} @ {p.captured_at}")

    print(f"\n=== Restock events (last 24h): {len(restocks)} ===")
    for r in restocks:
        print(f"  [{r.source}] {r.product_name_raw!r} @ {r.detected_at}")

    print(f"\n=== Latest news items: {len(news)} ===")
    for n in news:
        print(f"  [{n.source}] {n.title} — {n.url}")


if __name__ == "__main__":
    asyncio.run(main())
