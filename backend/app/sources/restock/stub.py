from datetime import datetime, timezone

from app.sources.base import RestockSignal, RestockSource


class StubRestockSource(RestockSource):
    """Used when no Discord bot token/channel is configured."""

    name = "stub"

    async def fetch_restocks(self) -> list[RestockSignal]:
        return [
            RestockSignal(
                product_name_raw="[stub] Scarlet & Violet Booster Bundle restocked",
                retailer="stub-retailer",
                source_ref="stub",
                message_text="Restock alert (stub data, no Discord source configured)",
                url=None,
                detected_at=datetime.now(timezone.utc),
            )
        ]
