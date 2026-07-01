import asyncio
import logging

import resend

from app.config import Settings
from app.delivery.base import Notifier

logger = logging.getLogger(__name__)


class ResendEmailNotifier(Notifier):
    name = "resend"

    def __init__(self, settings: Settings) -> None:
        resend.api_key = settings.resend_api_key
        self._from_email = settings.resend_from_email

    async def send_digest(self, to: str, subject: str, text_body: str, html_body: str | None) -> bool:
        try:
            # resend's SDK is sync; run it off the event loop thread.
            await asyncio.to_thread(
                resend.Emails.send,
                {
                    "from": self._from_email,
                    "to": [to],
                    "subject": subject,
                    "text": text_body,
                    "html": html_body or text_body,
                },
            )
            return True
        except Exception:
            logger.exception("resend send failed")
            return False
