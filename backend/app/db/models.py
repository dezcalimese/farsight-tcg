import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), index=True)
    set_name: Mapped[str] = mapped_column(String(255))
    set_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rarity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tcgplayer_product_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="card")


class SealedProduct(Base):
    __tablename__ = "sealed_products"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), index=True)
    set_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # booster box, ETB, blister, etc.
    tcgplayer_product_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="sealed_product")
    restock_events: Mapped[list["RestockEvent"]] = relationship(back_populates="sealed_product")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        CheckConstraint(
            "(card_id IS NOT NULL) != (sealed_product_id IS NOT NULL)",
            name="price_snapshot_exactly_one_item",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), nullable=True, index=True)
    sealed_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sealed_products.id"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(64))  # e.g. "tcgplayer"
    price_low: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_mid: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_high: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    market_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    card: Mapped[Card | None] = relationship(back_populates="price_snapshots")
    sealed_product: Mapped[SealedProduct | None] = relationship(back_populates="price_snapshots")


class RestockEvent(Base):
    __tablename__ = "restock_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    sealed_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sealed_products.id"), nullable=True, index=True
    )
    product_name_raw: Mapped[str] = mapped_column(String(255))  # as seen in the source, pre-matching
    retailer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(64))  # e.g. "discord"
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # channel id, message id, etc.
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    sealed_product: Mapped[SealedProduct | None] = relationship(back_populates="restock_events")


class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (
        CheckConstraint("url <> ''", name="news_item_url_not_empty"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(Text, unique=True)
    source: Mapped[str] = mapped_column(String(128))  # e.g. "pokebeach"
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
