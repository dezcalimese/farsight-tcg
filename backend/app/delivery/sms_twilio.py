import asyncio
import logging

from twilio.rest import Client

from app.config import Settings
from app.delivery.base import Notifier

logger = logging.getLogger(__name__)

_MAX_SMS_CHARS = 1500  # keep well under the ~1600-char concatenated-segment limit


class TwilioSmsNotifier(Notifier):
    name = "twilio"

    def __init__(self, settings: Settings) -> None:
        self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self._from_number = settings.twilio_from_number

    async def send_digest(self, to: str, subject: str, text_body: str, html_body: str | None) -> bool:
        body = f"{subject}\n\n{text_body}"
        if len(body) > _MAX_SMS_CHARS:
            body = body[: _MAX_SMS_CHARS - 1].rstrip() + "…"
        try:
            await asyncio.to_thread(
                self._client.messages.create,
                body=body,
                from_=self._from_number,
                to=to,
            )
            return True
        except Exception:
            logger.exception("twilio send failed")
            return False
