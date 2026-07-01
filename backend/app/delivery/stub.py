import logging

from app.delivery.base import Notifier

logger = logging.getLogger(__name__)


class StubNotifier(Notifier):
    """Used when a channel has no credentials configured. Logs instead of sending."""

    def __init__(self, channel: str) -> None:
        self.name = f"stub-{channel}"

    async def send_digest(self, subject: str, text_body: str, html_body: str | None) -> bool:
        logger.info("[STUB %s] would send digest: %s (%d chars text)", self.name, subject, len(text_body))
        return True
