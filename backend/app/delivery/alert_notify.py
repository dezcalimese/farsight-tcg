import logging

from app.config import Settings
from app.db.models import Subscriber
from app.delivery import get_email_notifier, get_sms_notifier

logger = logging.getLogger(__name__)


async def send_alert(settings: Settings, subscriber: Subscriber, message: str) -> bool:
    subject = "Farsight alert"
    notifier = get_email_notifier(settings) if subscriber.channel == "email" else get_sms_notifier(settings)
    to = subscriber.email if subscriber.channel == "email" else subscriber.phone
    return await notifier.send_digest(to, subject, message, f"<p>{message}</p>")
