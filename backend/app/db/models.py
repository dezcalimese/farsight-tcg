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


class Subscriber(Base):
    __tablename__ = "subscribers"
    __table_args__ = (
        CheckConstraint("cadence IN ('daily', 'weekly')", name="subscriber_cadence_valid"),
        CheckConstraint(
            "status IN ('pending_verification', 'active', 'unsubscribed')", name="subscriber_status_valid"
        ),
        # At least one contact method, and a channel can only be enabled if its contact is set.
        CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="subscriber_has_a_contact"),
        CheckConstraint("NOT email_enabled OR email IS NOT NULL", name="subscriber_email_enabled_needs_email"),
        CheckConstraint("NOT sms_enabled OR phone IS NOT NULL", name="subscriber_sms_enabled_needs_phone"),
        CheckConstraint("email_enabled OR sms_enabled", name="subscriber_at_least_one_channel_enabled"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    email_enabled: Mapped[bool] = mapped_column(default=True)
    sms_enabled: Mapped[bool] = mapped_column(default=False)
    cadence: Mapped[str] = mapped_column(String(16), default="daily")  # "daily" | "weekly"
    status: Mapped[str] = mapped_column(String(32), default="pending_verification", index=True)

    # Per-category digest mutes. Trending cards + top movers are muted together
    # ("market movers") since they're the same underlying price-move data.
    mute_movers: Mapped[bool] = mapped_column(default=False)
    mute_restocks: Mapped[bool] = mapped_column(default=False)
    mute_news: Mapped[bool] = mapped_column(default=False)

    confirm_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    confirm_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Holds the new email/phone while a "verify a second channel" flow is in
    # flight — promoted onto email/phone once confirm_token is redeemed.
    pending_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unsubscribe_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # Permanent capability token for the portfolio/settings pages — deliberately
    # separate from unsubscribe_token so leaking one link can't do the other's job.
    portfolio_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    holdings: Mapped[list["Holding"]] = relationship(back_populates="subscriber", cascade="all, delete-orphan")
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="subscriber", cascade="all, delete-orphan"
    )


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        CheckConstraint("(card_id IS NOT NULL) != (sealed_product_id IS NOT NULL)", name="holding_exactly_one_item"),
        CheckConstraint("quantity > 0", name="holding_quantity_positive"),
        CheckConstraint("purchase_price >= 0", name="holding_purchase_price_nonnegative"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    subscriber_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscribers.id"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), nullable=True, index=True)
    sealed_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sealed_products.id"), nullable=True, index=True
    )
    quantity: Mapped[int] = mapped_column(default=1)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2))
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriber: Mapped[Subscriber] = relationship(back_populates="holdings")
    card: Mapped[Card | None] = relationship()
    sealed_product: Mapped[SealedProduct | None] = relationship()


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('price_above', 'price_below', 'pct_move', 'restock')", name="alert_rule_type_valid"
        ),
        CheckConstraint(
            "card_id IS NOT NULL OR sealed_product_id IS NOT NULL OR watch_text IS NOT NULL",
            name="alert_rule_has_target",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    subscriber_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscribers.id"), index=True)
    rule_type: Mapped[str] = mapped_column(String(32))
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), nullable=True, index=True)
    sealed_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sealed_products.id"), nullable=True, index=True
    )
    # Free-text substring match against RestockEvent.product_name_raw for "restock" rules.
    watch_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Dollar threshold for price_above/price_below, percent threshold for pct_move.
    threshold: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Rolling window for pct_move rules only.
    window_hours: Mapped[int] = mapped_column(default=24)

    # Edge-triggered dedupe: once fired, don't refire until the condition
    # clears and re-triggers, so a price sitting above threshold doesn't
    # spam an alert every evaluation cycle.
    is_armed: Mapped[bool] = mapped_column(default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriber: Mapped[Subscriber] = relationship(back_populates="alert_rules")
    card: Mapped[Card | None] = relationship()
    sealed_product: Mapped[SealedProduct | None] = relationship()
