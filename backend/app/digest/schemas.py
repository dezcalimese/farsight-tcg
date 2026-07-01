from datetime import datetime

from pydantic import BaseModel


class PriceMove(BaseModel):
    item_name: str
    item_type: str  # "card" | "sealed_product"
    price_then: float
    price_now: float
    pct_change: float


class RestockHighlight(BaseModel):
    product_name: str
    retailer: str | None
    url: str | None
    detected_at: datetime


class NewsHighlight(BaseModel):
    title: str
    url: str
    source: str


class DigestData(BaseModel):
    generated_at: datetime
    period_days: int
    trending_cards: list[PriceMove]
    top_movers: list[PriceMove]
    restocks: list[RestockHighlight]
    news: list[NewsHighlight]

    @property
    def is_empty(self) -> bool:
        return not (self.trending_cards or self.top_movers or self.restocks or self.news)
