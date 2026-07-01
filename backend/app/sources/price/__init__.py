from app.config import Settings
from app.sources.base import PriceSource
from app.sources.price.stub import StubPriceSource
from app.sources.price.tcgplayer import TCGPlayerPriceSource


def get_price_source(settings: Settings) -> PriceSource:
    if settings.tcgplayer_configured:
        return TCGPlayerPriceSource(settings)
    return StubPriceSource()
