from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PricePoint:
    """One priced item at a point in time, keyed loosely for later matching to Card/SealedProduct."""

    item_name: str
    item_type: str  # "card" | "sealed_product"
    tcgplayer_product_id: str | None
    set_name: str | None
    price_low: float | None
    price_mid: float | None
    price_high: float | None
    market_price: float | None
    currency: str = "USD"


@dataclass
class RestockSignal:
    product_name_raw: str
    retailer: str | None
    source_ref: str | None
    message_text: str | None
    url: str | None
    detected_at: datetime


@dataclass
class NewsEntry:
    title: str
    url: str
    source: str
    summary: str | None
    published_at: datetime | None


class PriceSource(ABC):
    """Fetches current prices for cards and/or sealed product."""

    name: str

    @abstractmethod
    async def fetch_prices(self) -> list[PricePoint]:
        ...


class RestockSource(ABC):
    """Watches a channel for restock signal and returns new events since last poll."""

    name: str

    @abstractmethod
    async def fetch_restocks(self) -> list[RestockSignal]:
        ...


class NewsSource(ABC):
    """Pulls recent news items from a feed."""

    name: str

    @abstractmethod
    async def fetch_news(self) -> list[NewsEntry]:
        ...
