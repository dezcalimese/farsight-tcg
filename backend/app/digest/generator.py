from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Card, NewsItem, PriceSnapshot, RestockEvent, SealedProduct
from app.digest.schemas import DigestData, NewsHighlight, PriceMove, RestockHighlight

MAX_TRENDING_CARDS = 3
MAX_TOP_MOVERS = 5
MAX_RESTOCKS = 5
MAX_NEWS = 2


async def _price_moves(session: AsyncSession, since: datetime) -> list[PriceMove]:
    result = await session.execute(
        select(PriceSnapshot, Card.name, SealedProduct.name)
        .outerjoin(Card, PriceSnapshot.card_id == Card.id)
        .outerjoin(SealedProduct, PriceSnapshot.sealed_product_id == SealedProduct.id)
        .where(PriceSnapshot.captured_at >= since)
        .where(PriceSnapshot.market_price.is_not(None))
        .order_by(PriceSnapshot.captured_at.asc())
    )

    # Group snapshots per item, keep first and last seen in the window.
    by_item: dict[tuple[str, str], dict] = {}
    for snapshot, card_name, sealed_name in result.all():
        if snapshot.card_id:
            key = ("card", str(snapshot.card_id))
            name = card_name
        else:
            key = ("sealed_product", str(snapshot.sealed_product_id))
            name = sealed_name

        entry = by_item.setdefault(key, {"name": name, "first": snapshot, "last": snapshot})
        entry["last"] = snapshot

    moves: list[PriceMove] = []
    for (item_type, _item_id), entry in by_item.items():
        first, last = entry["first"], entry["last"]
        if first is last:
            continue  # need at least two data points to call it a "move"
        price_then = float(first.market_price)
        price_now = float(last.market_price)
        if price_then == 0:
            continue
        pct_change = (price_now - price_then) / price_then * 100
        moves.append(
            PriceMove(
                item_name=entry["name"] or "Unknown item",
                item_type=item_type,
                price_then=price_then,
                price_now=price_now,
                pct_change=round(pct_change, 2),
            )
        )
    return moves


async def _restock_highlights(session: AsyncSession, since: datetime) -> list[RestockHighlight]:
    result = await session.execute(
        select(RestockEvent)
        .where(RestockEvent.detected_at >= since)
        .order_by(RestockEvent.detected_at.desc())
    )
    seen_products: set[str] = set()
    highlights: list[RestockHighlight] = []
    for event in result.scalars().all():
        dedupe_key = event.product_name_raw.lower()
        if dedupe_key in seen_products:
            continue
        seen_products.add(dedupe_key)
        highlights.append(
            RestockHighlight(
                product_name=event.product_name_raw,
                retailer=event.retailer,
                url=event.url,
                detected_at=event.detected_at,
            )
        )
        if len(highlights) >= MAX_RESTOCKS:
            break
    return highlights


async def _news_highlights(session: AsyncSession, since: datetime) -> list[NewsHighlight]:
    result = await session.execute(
        select(NewsItem)
        .where(NewsItem.fetched_at >= since)
        .order_by(NewsItem.published_at.desc().nulls_last(), NewsItem.fetched_at.desc())
        .limit(MAX_NEWS)
    )
    return [
        NewsHighlight(title=item.title, url=item.url, source=item.source)
        for item in result.scalars().all()
    ]


async def generate_digest(session: AsyncSession, period_days: int = 7) -> DigestData:
    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    moves = await _price_moves(session, since)
    gainers = sorted((m for m in moves if m.pct_change > 0), key=lambda m: m.pct_change, reverse=True)
    trending_cards = [m for m in gainers if m.item_type == "card"][:MAX_TRENDING_CARDS]
    top_movers = sorted(moves, key=lambda m: abs(m.pct_change), reverse=True)[:MAX_TOP_MOVERS]

    restocks = await _restock_highlights(session, since)
    news = await _news_highlights(session, since)

    return DigestData(
        generated_at=datetime.now(timezone.utc),
        period_days=period_days,
        trending_cards=trending_cards,
        top_movers=top_movers,
        restocks=restocks,
        news=news,
    )
