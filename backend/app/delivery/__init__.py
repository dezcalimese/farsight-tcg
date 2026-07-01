from app.config import Settings
from app.delivery.base import Notifier
from app.delivery.discord_webhook import DiscordWebhookNotifier
from app.delivery.email_resend import ResendEmailNotifier
from app.delivery.sms_twilio import TwilioSmsNotifier
from app.delivery.stub import StubNotifier


def get_notifiers(settings: Settings) -> list[Notifier]:
    """Returns one notifier per configured channel. Falls back to a logging
    stub for any channel missing credentials, so the send job never blocks
    on missing keys."""
    notifiers: list[Notifier] = []

    notifiers.append(ResendEmailNotifier(settings) if settings.resend_configured else StubNotifier("email"))
    notifiers.append(TwilioSmsNotifier(settings) if settings.twilio_configured else StubNotifier("sms"))
    notifiers.append(
        DiscordWebhookNotifier(settings) if settings.discord_webhook_configured else StubNotifier("discord")
    )

    return notifiers
