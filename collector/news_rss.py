"""Fetch World Cup news from RSS feeds (no API key needed)."""

import logging
import httpx
import feedparser
from datetime import datetime, timezone
from time import mktime
from urllib.parse import urlparse

from config import RSS_FEEDS, WC_KEYWORDS
from db.database import insert_news

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (world-cup-tickets personal dashboard)"}


def _is_relevant(title: str) -> bool:
    """Check if a news item is World Cup related."""
    t = title.lower()
    return any(kw in t for kw in WC_KEYWORDS)


def collect() -> int:
    """Fetch from all configured RSS feeds. Returns count of new items."""
    total = 0
    for name, feed_url in RSS_FEEDS.items():
        try:
            total += _collect_feed(name, feed_url)
        except Exception as e:
            log.error(f"[news] {name}: {e}")
    return total


def _collect_feed(source_name: str, feed_url: str, limit: int = 30) -> int:
    response = httpx.get(feed_url, headers=HEADERS, follow_redirects=True, timeout=15)
    response.raise_for_status()
    feed = feedparser.parse(response.text)

    inserted = 0
    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        if not title or not link:
            continue

        # Filter for World Cup relevance
        if not _is_relevant(title):
            continue

        published_at = None
        for date_field in ("published_parsed", "updated_parsed"):
            parsed = entry.get(date_field)
            if parsed:
                try:
                    dt = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                    published_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OverflowError):
                    pass
                break

        slug = urlparse(link).path.rstrip("/").split("/")[-1] or link

        new = insert_news(
            source_name=source_name,
            title=title,
            url=link,
            published_at=published_at,
            external_id=slug,
        )
        if new:
            inserted += 1

    log.info(f"[news] {source_name}: +{inserted} new items")
    return inserted
