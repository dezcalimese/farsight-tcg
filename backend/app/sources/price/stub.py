import random

from app.sources.base import PricePoint, PriceSource

_STUB_ITEMS = [
    ("Charizard ex - Obsidian Flames", "card"),
    ("Pikachu VMAX - Vivid Voltage", "card"),
    ("Scarlet & Violet Booster Box", "sealed_product"),
    ("151 Elite Trainer Box", "sealed_product"),
]


class StubPriceSource(PriceSource):
    """Used when no TCGPlayer credentials are configured, so the app still runs end-to-end."""

    name = "stub"

    async def fetch_prices(self) -> list[PricePoint]:
        return [
            PricePoint(
                item_name=name,
                item_type=item_type,
                tcgplayer_product_id=None,
                set_name=None,
                price_low=round(random.uniform(5, 50), 2),
                price_mid=round(random.uniform(50, 150), 2),
                price_high=round(random.uniform(150, 400), 2),
                market_price=round(random.uniform(50, 150), 2),
            )
            for name, item_type in _STUB_ITEMS
        ]
