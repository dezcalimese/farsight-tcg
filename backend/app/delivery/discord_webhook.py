import logging

import httpx

from app.config import Settings
from app.delivery.base import Notifier

logger = logging.getLogger(__name__)

_MAX_CONTENT_CHARS = 1900  # Discord message content limit is 2000


class DiscordWebhookNotifier(Notifier):
    name = "discord"

    def __init__(self, settings: Settings) -> None:
        self._webhook_url = settings.discord_webhook_url

    async def send_digest(self, to: str, subject: str, text_body: str, html_body: str | None) -> bool:
        # `to` is unused — Discord is a single static broadcast channel, not per-recipient.
        content = f"**{subject}**\n```{text_body}```"
        if len(content) > _MAX_CONTENT_CHARS:
            content = content[: _MAX_CONTENT_CHARS - 4].rstrip() + "...```"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self._webhook_url, json={"content": content})
                resp.raise_for_status()
            return True
        except httpx.HTTPError:
            logger.exception("discord webhook send failed")
            return False
