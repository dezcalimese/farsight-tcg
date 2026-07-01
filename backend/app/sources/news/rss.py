from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx

from app.config import Settings
from app.sources.base import NewsEntry, NewsSource


class RssNewsSource(NewsSource):
    """Pulls from a small curated set of RSS feeds. Requires no API key."""

    name = "rss"

    def __init__(self, settings: Settings) -> None:
        self._feed_urls = settings.news_rss_feed_list

    async def fetch_news(self) -> list[NewsEntry]:
        entries: list[NewsEntry] = []
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for feed_url in self._feed_urls:
                try:
                    resp = await client.get(
                        feed_url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                            )
                        },
                    )
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue
                parsed = feedparser.parse(resp.content)
                source_name = parsed.feed.get("title", feed_url)
                for item in parsed.entries:
                    published_at = None
                    if getattr(item, "published_parsed", None):
                        published_at = datetime.fromtimestamp(
                            mktime(item.published_parsed), tz=timezone.utc
                        )
                    entries.append(
                        NewsEntry(
                            title=item.get("title", "Untitled"),
                            url=item.get("link", ""),
                            source=source_name,
                            summary=item.get("summary"),
                            published_at=published_at,
                        )
                    )
        return [e for e in entries if e.url]
