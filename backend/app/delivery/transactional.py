import logging

from app.config import Settings
from app.delivery import get_email_notifier, get_sms_notifier

logger = logging.getLogger(__name__)


async def send_magic_link(settings: Settings, to_email: str, confirm_url: str) -> bool:
    subject = "Confirm your Farsight digest"
    text = f"Tap to confirm your Pokemon TCG digest signup:\n\n{confirm_url}\n\nThis link expires in 30 minutes."
    html = (
        f'<p>Tap to confirm your Pokemon TCG digest signup:</p>'
        f'<p><a href="{confirm_url}">{confirm_url}</a></p>'
        f'<p>This link expires in 30 minutes.</p>'
    )
    notifier = get_email_notifier(settings)
    return await notifier.send_digest(to_email, subject, text, html)


async def send_otp_sms(settings: Settings, to_phone: str, code: str) -> bool:
    subject = "Farsight code"
    text = f"Your Farsight confirmation code is {code}. It expires in 10 minutes."
    notifier = get_sms_notifier(settings)
    return await notifier.send_digest(to_phone, subject, text, None)
