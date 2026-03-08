"""Fetch ticket-related posts from Reddit (no auth needed)."""

import re
import logging
import httpx
from datetime import datetime, timezone

from config import REDDIT_SUBS
from db.database import insert_reddit_post

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "world-cup-tickets/1.0 (personal dashboard)"}

# Simple keyword-based sentiment detection
BUY_KEYWORDS = re.compile(r"\b(wtb|want to buy|looking for|need tickets?|buying)\b", re.I)
SELL_KEYWORDS = re.compile(r"\b(wts|want to sell|selling|for sale|have tickets?)\b", re.I)


def _classify_sentiment(title: str) -> str:
    has_buy = bool(BUY_KEYWORDS.search(title))
    has_sell = bool(SELL_KEYWORDS.search(title))
    if has_buy and not has_sell:
        return "buying"
    if has_sell and not has_buy:
        return "selling"
    return "neutral"


def collect() -> int:
    """Fetch top posts from ticket-related subreddits. Returns count of new posts."""
    total = 0
    for sub in REDDIT_SUBS:
        try:
            total += _collect_sub(sub)
        except Exception as e:
            log.error(f"[reddit] r/{sub}: {e}")
    return total


def _collect_sub(subreddit: str, limit: int = 25) -> int:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    response = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
    response.raise_for_status()

    posts = response.json().get("data", {}).get("children", [])
    inserted = 0

    for post in posts:
        data = post["data"]
        published_at = datetime.fromtimestamp(
            data["created_utc"], tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

        title = data["title"]
        sentiment = _classify_sentiment(title)

        new = insert_reddit_post(
            subreddit=subreddit,
            title=title,
            url=f"https://www.reddit.com{data['permalink']}",
            score=data.get("score", 0),
            num_comments=data.get("num_comments", 0),
            published_at=published_at,
            external_id=data["id"],
            sentiment=sentiment,
        )
        if new:
            inserted += 1

    log.info(f"[reddit] r/{subreddit}: +{inserted} new posts")
    return inserted
