from app.config import Settings
from app.delivery.base import Notifier
from app.delivery.discord_webhook import DiscordWebhookNotifier
from app.delivery.email_resend import ResendEmailNotifier
from app.delivery.sms_twilio import TwilioSmsNotifier
from app.delivery.stub import StubNotifier


def get_email_notifier(settings: Settings) -> Notifier:
    if settings.resend_configured:
        return ResendEmailNotifier(settings)
    return StubNotifier("email")


def get_sms_notifier(settings: Settings) -> Notifier:
    if settings.twilio_configured:
        return TwilioSmsNotifier(settings)
    return StubNotifier("sms")


def get_discord_notifier(settings: Settings) -> Notifier:
    if settings.discord_webhook_configured:
        return DiscordWebhookNotifier(settings)
    return StubNotifier("discord")
