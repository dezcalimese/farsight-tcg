import logging

from app.config import Settings
from app.db.models import Subscriber
from app.delivery import get_email_notifier, get_sms_notifier

logger = logging.getLogger(__name__)


async def send_alert(settings: Settings, subscriber: Subscriber, message: str) -> bool:
    """Sends to every channel the subscriber has enabled. Returns True if at
    least one channel succeeded."""
    subject = "Farsight alert"
    ok = False
    if subscriber.email_enabled:
        ok = await get_email_notifier(settings).send_digest(
            subscriber.email, subject, message, f"<p>{message}</p>"
        ) or ok
    if subscriber.sms_enabled:
        ok = await get_sms_notifier(settings).send_digest(
            subscriber.phone, subject, message, f"<p>{message}</p>"
        ) or ok
    return ok
