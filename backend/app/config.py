from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    env: str = "development"
    database_url: str = "postgresql+asyncpg://farsight:farsight@localhost:5432/farsight"
    redis_url: str = "redis://localhost:6379/0"
    base_url: str = "http://localhost:8000"  # used to build magic-link/unsubscribe URLs

    # TCGPlayer (price source)
    tcgplayer_client_id: str | None = None
    tcgplayer_client_secret: str | None = None

    # Discord (restock source)
    discord_bot_token: str | None = None
    discord_restock_channel_ids: str | None = None  # comma-separated channel IDs

    # News (RSS) — no key required, but URLs are configurable.
    # PokeBeach and the official Pokemon.com feed are currently behind
    # Cloudflare/Incapsula bot challenges that block plain HTTP fetches; per
    # the PRD we don't bypass bot detection, so r/PokemonTCG's Atom feed is
    # the working default. Swap in PokeBeach/official feeds here once/if
    # they're reachable again.
    news_rss_feeds: str = "https://www.reddit.com/r/PokemonTCG/.rss"

    # Delivery
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    discord_webhook_url: str | None = None

    # Digest send schedule. Each subscriber picks daily or weekly at signup;
    # these settings only control what time of day/week the two send jobs run.
    digest_send_hour_utc: int = 13
    digest_send_weekday: int = 0  # 0=Monday, for the weekly job

    @property
    def news_rss_feed_list(self) -> list[str]:
        return [f.strip() for f in self.news_rss_feeds.split(",") if f.strip()]

    @property
    def discord_restock_channel_id_list(self) -> list[int]:
        if not self.discord_restock_channel_ids:
            return []
        return [int(c.strip()) for c in self.discord_restock_channel_ids.split(",") if c.strip()]

    @property
    def tcgplayer_configured(self) -> bool:
        return bool(self.tcgplayer_client_id and self.tcgplayer_client_secret)

    @property
    def discord_configured(self) -> bool:
        return bool(self.discord_bot_token and self.discord_restock_channel_id_list)

    @property
    def resend_configured(self) -> bool:
        return bool(self.resend_api_key and self.resend_from_email)

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)

    @property
    def discord_webhook_configured(self) -> bool:
        return bool(self.discord_webhook_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
