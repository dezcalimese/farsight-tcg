import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Card, NewsItem, PriceSnapshot, RestockEvent, SealedProduct
from app.sources.base import NewsSource, PriceSource, RestockSource

logger = logging.getLogger(__name__)


async def _get_or_create_card(
    session: AsyncSession, name: str, tcgplayer_product_id: str | None, image_url: str | None
) -> Card:
    card: Card | None = None
    if tcgplayer_product_id:
        result = await session.execute(select(Card).where(Card.tcgplayer_product_id == tcgplayer_product_id))
        card = result.scalar_one_or_none()
    if card is None:
        result = await session.execute(select(Card).where(Card.name == name))
        card = result.scalar_one_or_none()
    if card is None:
        card = Card(name=name, set_name="Unknown", tcgplayer_product_id=tcgplayer_product_id)
        session.add(card)
    if image_url:
        card.image_url = image_url
    await session.flush()
    return card


async def _get_or_create_sealed_product(
    session: AsyncSession, name: str, tcgplayer_product_id: str | None, image_url: str | None
) -> SealedProduct:
    product: SealedProduct | None = None
    if tcgplayer_product_id:
        result = await session.execute(
            select(SealedProduct).where(SealedProduct.tcgplayer_product_id == tcgplayer_product_id)
        )
        product = result.scalar_one_or_none()
    if product is None:
        result = await session.execute(select(SealedProduct).where(SealedProduct.name == name))
        product = result.scalar_one_or_none()
    if product is None:
        product = SealedProduct(name=name, tcgplayer_product_id=tcgplayer_product_id)
        session.add(product)
    if image_url:
        product.image_url = image_url
    await session.flush()
    return product


async def ingest_prices(session: AsyncSession, source: PriceSource) -> int:
    points = await source.fetch_prices()
    for point in points:
        if point.item_type == "sealed_product":
            item = await _get_or_create_sealed_product(
                session, point.item_name, point.tcgplayer_product_id, point.image_url
            )
            snapshot = PriceSnapshot(sealed_product_id=item.id, source=source.name)
        else:
            item = await _get_or_create_card(
                session, point.item_name, point.tcgplayer_product_id, point.image_url
            )
            snapshot = PriceSnapshot(card_id=item.id, source=source.name)
        snapshot.price_low = point.price_low
        snapshot.price_mid = point.price_mid
        snapshot.price_high = point.price_high
        snapshot.market_price = point.market_price
        snapshot.currency = point.currency
        session.add(snapshot)
    await session.commit()
    logger.info("ingested %d price points from %s", len(points), source.name)
    return len(points)


async def ingest_restocks(session: AsyncSession, source: RestockSource) -> int:
    signals = await source.fetch_restocks()
    inserted = 0
    for signal in signals:
        if signal.source_ref:
            existing = await session.execute(
                select(RestockEvent).where(RestockEvent.source_ref == signal.source_ref)
            )
            if existing.scalar_one_or_none():
                continue
        event = RestockEvent(
            product_name_raw=signal.product_name_raw,
            retailer=signal.retailer,
            source=source.name,
            source_ref=signal.source_ref,
            message_text=signal.message_text,
            url=signal.url,
            detected_at=signal.detected_at,
        )
        session.add(event)
        inserted += 1
    await session.commit()
    logger.info("ingested %d restock events from %s", inserted, source.name)
    return inserted


async def ingest_news(session: AsyncSession, source: NewsSource) -> int:
    entries = await source.fetch_news()
    inserted = 0
    for entry in entries:
        stmt = (
            pg_insert(NewsItem)
            .values(
                title=entry.title,
                url=entry.url,
                source=entry.source,
                summary=entry.summary,
                published_at=entry.published_at,
            )
            .on_conflict_do_nothing(index_elements=[NewsItem.url])
        )
        result = await session.execute(stmt)
        inserted += result.rowcount or 0
    await session.commit()
    logger.info("ingested %d news items from %s", inserted, source.name)
    return inserted


async def run_full_ingest(session: AsyncSession, settings: Settings) -> dict[str, int]:
    from app.sources.news import get_news_source
    from app.sources.price import get_price_source
    from app.sources.restock import get_restock_source

    price_count = await ingest_prices(session, get_price_source(settings))
    restock_count = await ingest_restocks(session, get_restock_source(settings))
    news_count = await ingest_news(session, get_news_source(settings))
    return {"prices": price_count, "restocks": restock_count, "news": news_count}
