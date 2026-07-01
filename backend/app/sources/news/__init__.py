from app.config import Settings
from app.sources.base import NewsSource
from app.sources.news.rss import RssNewsSource


def get_news_source(settings: Settings) -> NewsSource:
    return RssNewsSource(settings)
