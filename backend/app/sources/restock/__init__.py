from app.config import Settings
from app.sources.base import RestockSource
from app.sources.restock.discord_channel import DiscordChannelRestockSource
from app.sources.restock.stub import StubRestockSource


def get_restock_source(settings: Settings) -> RestockSource:
    if settings.discord_configured:
        return DiscordChannelRestockSource(settings)
    return StubRestockSource()
