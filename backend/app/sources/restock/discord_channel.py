import re
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.sources.base import RestockSignal, RestockSource

RESTOCK_KEYWORDS = re.compile(
    r"\b(restock|in stock|back in stock|available now|just dropped|live now)\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://\S+")


class DiscordChannelRestockSource(RestockSource):
    """Polls configured Discord channels via the bot REST API for restock-shaped messages.

    Uses REST polling (not the gateway) since this runs on a schedule, not
    as a long-lived connection.
    """

    name = "discord"
    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, settings: Settings, lookback_messages: int = 50) -> None:
        self._token = settings.discord_bot_token
        self._channel_ids = settings.discord_restock_channel_id_list
        self._lookback_messages = lookback_messages

    async def _fetch_channel_messages(self, client: httpx.AsyncClient, channel_id: int) -> list[dict]:
        resp = await client.get(
            f"{self.BASE_URL}/channels/{channel_id}/messages",
            params={"limit": self._lookback_messages},
            headers={"Authorization": f"Bot {self._token}"},
        )
        resp.raise_for_status()
        return resp.json()

    async def fetch_restocks(self) -> list[RestockSignal]:
        signals: list[RestockSignal] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for channel_id in self._channel_ids:
                messages = await self._fetch_channel_messages(client, channel_id)
                for msg in messages:
                    content = msg.get("content", "")
                    if not RESTOCK_KEYWORDS.search(content):
                        continue
                    url_match = URL_RE.search(content)
                    signals.append(
                        RestockSignal(
                            product_name_raw=content[:255],
                            retailer=None,
                            source_ref=f"{channel_id}:{msg['id']}",
                            message_text=content,
                            url=url_match.group(0) if url_match else None,
                            detected_at=datetime.fromisoformat(
                                msg["timestamp"].replace("Z", "+00:00")
                            ).astimezone(timezone.utc),
                        )
                    )
        return signals
